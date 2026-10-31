"""Gemini LLM service for language synthesis grounded strictly in retrieved context.

Uses raw httpx REST calls to the Gemini 1.5 Flash API — no google.generativeai SDK
(keeps the container footprint under Render's 512 MB limit).
"""

import hashlib
import json
import logging
import asyncio
from collections import OrderedDict
from typing import List, Optional, Dict, Any

import httpx

from app.config import get_settings
from app.schemas import SourceCitation

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Constants & Endpoint Helper
# ---------------------------------------------------------------------------
def get_gemini_endpoint() -> str:
    """Return the Gemini generateContent REST URL for the configured model."""
    model = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite") or "gemini-3.5-flash-lite"
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

GEMINI_GENERATE_ENDPOINT = get_gemini_endpoint()

_REQUEST_TIMEOUT = 25.0  # seconds
_MAX_RETRIES = 2
_RETRYABLE_STATUS_CODES = {429, 500, 503}

# ---------------------------------------------------------------------------
# Response cache (LRU, max 50 entries) keyed by (question_hash, sources_hash)
# ---------------------------------------------------------------------------
_answer_cache: OrderedDict[str, str] = OrderedDict()
_ANSWER_CACHE_MAX = 50


def _cache_key(question: str, sources: List[SourceCitation]) -> str:
    """Build a deterministic cache key from question + source texts."""
    q_hash = hashlib.sha256(question.encode("utf-8")).hexdigest()[:16]
    s_hash = hashlib.sha256(
        "||".join(s.chunk_text for s in sources).encode("utf-8")
    ).hexdigest()[:16]
    return f"{q_hash}:{s_hash}"


def _put_cache(key: str, value: str) -> None:
    """Insert into LRU answer cache, evicting oldest if over capacity."""
    _answer_cache[key] = value
    _answer_cache.move_to_end(key)
    while len(_answer_cache) > _ANSWER_CACHE_MAX:
        _answer_cache.popitem(last=False)


# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_TEMPLATE = """\
You are KisanSathi Rajasthan (किसान साथी राजस्थान), an expert agricultural AI assistant \
for farmers and agricultural researchers in Rajasthan.

KNOWLEDGE GROUNDING & RESPONSE INSTRUCTIONS:
1. When RETRIEVED KNOWLEDGE BASE PASSAGES below contain relevant information, prioritize and ground your diagnosis, crop recommendations, chemical names, and dosages directly in them, citing sources as [1], [2], etc.
2. If the retrieved passages do NOT cover the question (or are only partially relevant), use your authoritative agronomic knowledge (ICAR, CAZRI Jodhpur, Rajasthan Agricultural Universities Package of Practices, soil science, irrigation engineering, and plant nutrition) to provide a thorough, accurate, and deeply scientific answer.
3. For technical questions (such as Leaching Requirement formulas, EC/salinity dynamics, soil hardpan mitigation, drip emitter wetting patterns, fertigation, and micronutrient lockout in high pH/calcareous soils), explain the core principles, formulas/calculations, and step-by-step actionable recommendations clearly.
4. For crop diseases and pest problems without retrieved sources, provide standard ICAR / Rajasthan state recommended active ingredients with safe dosages, and advise confirming locally with a Krishi Vigyan Kendra (KVK).
5. Only say you do not know if the question is completely non-agricultural or nonsensical. Never refuse a legitimate farming, soil, crop, or irrigation question.
6. Respond in {language} (if the user asks in English, respond in English; if in Hindi, respond in Hindi).
7. Keep the tone respectful, professional, and actionable for Rajasthan farming conditions.
8. Emphasize that your advice is decision-support guidance, and major chemical or structural changes should be verified with local soil testing or the nearest KVK.
11. BE CONCISE: at most ~150 words, in short bullet points. For crop disease/pest problems cover only the 1-2 most
    relevant conditions (what it may be / what to do / prevention); for other questions (sowing, fertilizer, prices,
    weather, irrigation) answer the question directly. Use simple "**bold**" labels only; no headings or rules.
13. STRUCTURED DATA below (mandi prices, weather/irrigation, yield) is live data: quote its numbers with units and
    dates, and state that prices/yields are estimates, not guarantees. If STRUCTURED DATA is empty, do not invent any.
12. If the symptoms are ambiguous (several causes possible), end with ONE short question asking the farmer
    for the detail that would help most (e.g. which leaves are affected, or spots vs. curling).

FARMER PROFILE CONTEXT:
- District: {district}
- Tehsil: {tehsil}
- Crop: {crop}
- Land size: {land_hectare} ha
- Irrigation: {irrigation}
- Sowing Date: {sowing_date}

STRUCTURED DATA:
{structured_data}

RETRIEVED KNOWLEDGE BASE PASSAGES:
{retrieved_passages}
"""


# ---------------------------------------------------------------------------
# Passage formatting helper
# ---------------------------------------------------------------------------

def _format_passages(sources: List[SourceCitation]) -> str:
    """Format SourceCitations into numbered passages for the prompt."""
    if not sources:
        return "(No relevant passages retrieved.)"
    return "\n\n".join(
        f"[{i + 1}] {s.doc_title} ({s.source}):\n{s.chunk_text}"
        for i, s in enumerate(sources)
    )


def _build_fallback_response(
    sources: List[SourceCitation],
    language: str,
    notice: bool = False,
) -> str:
    """
    Build a direct-passages response when the LLM is unavailable.

    Args:
        sources: Retrieved source citations.
        language: Response language ('hi' or 'en').
        notice: Whether to prepend a service-notice header.

    Returns:
        Formatted string of source passages.
    """
    passages_text = _format_passages(sources)

    if not sources:
        if language == "en":
            return (
                "I am not sure based on verified records. "
                "Please contact your nearest Krishi Vigyan Kendra (KVK)."
            )
        return (
            "मुझे इस विषय में सत्यापित जानकारी नहीं मिली है। "
            "कृपया अपने नजदीकी कृषि विज्ञान केंद्र (KVK) से संपर्क करें।"
        )

    if notice:
        if language == "en":
            return (
                "Service notice: Showing retrieved reference directly:\n\n"
                + passages_text
            )
        return "प्रामाणिक संदर्भ विवरण:\n\n" + passages_text

    if language == "en":
        return (
            "Information retrieved from verified agricultural sources:\n\n"
            + passages_text
        )
    return "कृषि वैज्ञानिक स्रोतों से प्राप्त जानकारी:\n\n" + passages_text


# ---------------------------------------------------------------------------
# Main generation function
# ---------------------------------------------------------------------------

async def generate_grounded_answer(
    question: str,
    sources: List[SourceCitation],
    farmer_profile: Optional[Dict[str, Any]] = None,
    structured_data: Optional[Dict[str, Any]] = None,
    language: str = "hi",
) -> str:
    """
    Generate an answer using Gemini 1.5 Flash grounded strictly on retrieved sources.

    Features:
        * Response caching (LRU, max 50 entries).
        * Retries with exponential backoff on 429/500/503.
        * 15-second request timeout.
        * Graceful fallback to raw passages if all retries fail.
        * In test mode, returns passages directly without API calls.

    Args:
        question: The farmer's question.
        sources: Retrieved SourceCitation objects from the RAG pipeline.
        farmer_profile: Optional dict with district, tehsil, crop, etc.
        structured_data: Optional additional structured data (prices, yield, etc.).
        language: Response language — 'hi' (Hindi) or 'en' (English).

    Returns:
        Generated answer string.
    """
    profile = farmer_profile or {}
    passages_text = _format_passages(sources)

    # ---- Test mode or missing API key: direct passages ----
    if not settings.GEMINI_API_KEY or settings.ENVIRONMENT == "test":
        return _build_fallback_response(sources, language)

    # ---- Check response cache ----
    c_key = _cache_key(question, sources)
    if c_key in _answer_cache:
        _answer_cache.move_to_end(c_key)
        return _answer_cache[c_key]

    # ---- Build prompt ----
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        language="Hindi" if language == "hi" else "English",
        district=profile.get("district", "Rajasthan"),
        tehsil=profile.get("tehsil", "-"),
        crop=profile.get("crop", "-"),
        land_hectare=profile.get("land_hectare", "-"),
        irrigation=profile.get("irrigation", "-"),
        sowing_date=profile.get("sowing_date", "-"),
        structured_data=json.dumps(structured_data or {}, ensure_ascii=False),
        retrieved_passages=passages_text,
    )

    request_body = {
        "contents": [
            {
                "parts": [
                    {"text": system_prompt},
                    {"text": f"Farmer question: {question}"},
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 900,
        },
    }

    # ---- Call Gemini with retries ----
    last_error: Optional[Exception] = None
    for attempt in range(_MAX_RETRIES):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    get_gemini_endpoint(),
                    json=request_body,
                    headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                    timeout=_REQUEST_TIMEOUT,
                )

                if resp.status_code in _RETRYABLE_STATUS_CODES:
                    backoff = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(
                        "Gemini API returned %d (attempt %d/%d). Retrying in %ds...",
                        resp.status_code,
                        attempt + 1,
                        _MAX_RETRIES,
                        backoff,
                    )
                    last_error = httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )
                    await asyncio.sleep(backoff)
                    continue

                resp.raise_for_status()
                data = resp.json()

                # Extract text from Gemini response
                candidates = data.get("candidates", [])
                if not candidates:
                    logger.warning("Gemini returned no candidates.")
                    return _build_fallback_response(sources, language, notice=True)

                parts = candidates[0].get("content", {}).get("parts", [])
                answer_text = "".join(p.get("text", "") for p in parts).strip()

                if not answer_text:
                    logger.warning("Gemini returned empty answer text.")
                    return _build_fallback_response(sources, language, notice=True)

                # Cache the answer
                _put_cache(c_key, answer_text)
                return answer_text

        except httpx.TimeoutException:
            backoff = 2 ** attempt
            logger.warning(
                "Gemini request timed out (attempt %d/%d). Retrying in %ds...",
                attempt + 1,
                _MAX_RETRIES,
                backoff,
            )
            last_error = httpx.TimeoutException("Request timed out")
            await asyncio.sleep(backoff)
        except httpx.HTTPStatusError as exc:
            # Non-retryable HTTP error
            logger.error(
                "Gemini API error %d: %s",
                exc.response.status_code,
                exc.response.text[:300],
            )
            last_error = exc
            break
        except Exception as exc:
            logger.error("Gemini generation failed: %s", exc)
            last_error = exc
            break

    # ---- All retries exhausted: graceful fallback ----
    logger.warning(
        "All %d Gemini retries exhausted (last error: %s). Falling back to direct passages.",
        _MAX_RETRIES,
        last_error,
    )
    return _build_fallback_response(sources, language, notice=True)
