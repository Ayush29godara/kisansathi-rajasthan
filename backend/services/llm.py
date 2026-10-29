"""Gemini LLM service for language synthesis grounded strictly in retrieved context."""

import logging
from typing import List, Optional, Dict, Any
from app.config import get_settings
from app.schemas import SourceCitation

logger = logging.getLogger(__name__)
settings = get_settings()


SYSTEM_PROMPT_TEMPLATE = """You are KisanSathi Rajasthan (किसान साथी राजस्थान), a supportive AI assistant for smallholder farmers in Rajasthan.
CRITICAL SAFETY & HONESTY INSTRUCTIONS:
1. Ground every statement STRICTLY in the provided Sources or Structured Data below.
2. NEVER invent numbers, chemical pesticide names, or dosage recommendations.
3. Treatment and dosage information MUST come verbatim from the retrieved sources.
4. If the retrieved sources do not contain an answer or you are uncertain, respond honestly:
   "मुझे इस विषय में पूरी जानकारी नहीं है, कृपया अपने नजदीकी कृषि विज्ञान केंद्र (KVK) से संपर्क करें।" (or English equivalent).
5. Always explain in the user's requested language ({language}) in clear, respectful, and accessible language.
6. Emphasize that your advice is decision-support guidance, not a substitute for an expert.

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


async def generate_grounded_answer(
    question: str,
    sources: List[SourceCitation],
    farmer_profile: Optional[Dict[str, Any]] = None,
    structured_data: Optional[Dict[str, Any]] = None,
    language: str = "hi",
) -> str:
    """
    Generate an answer using Gemini 1.5 Flash grounded strictly on retrieved sources.
    
    If Gemini API fails, times out, or is unconfigured, falls back immediately
    to displaying the retrieved passages directly without failing the request.
    """
    profile = farmer_profile or {}
    passages_text = "\n\n".join(
        [f"[{i+1}] {s.doc_title} ({s.source}):\n{s.chunk_text}" for i, s in enumerate(sources)]
    )

    if not passages_text:
        if language == "en":
            return "I am not sure based on verified records. Please contact your nearest Krishi Vigyan Kendra (KVK)."
        return "मुझे इस विषय में सत्यापित जानकारी नहीं मिली है। कृपया अपने नजदीकी कृषि विज्ञान केंद्र (KVK) से संपर्क करें।"

    if not settings.GEMINI_API_KEY or settings.ENVIRONMENT == "test":
        # Fallback to direct passages if API key is not yet provided or in test environment
        if language == "en":
            return f"Information retrieved from verified agricultural sources:\n\n{passages_text}"
        return f"कृषि वैज्ञानिक स्रोतों से प्राप्त जानकारी:\n\n{passages_text}"

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)

        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            language="Hindi" if language == "hi" else "English",
            district=profile.get("district", "Rajasthan"),
            tehsil=profile.get("tehsil", "-"),
            crop=profile.get("crop", "-"),
            land_hectare=profile.get("land_hectare", "-"),
            irrigation=profile.get("irrigation", "-"),
            sowing_date=profile.get("sowing_date", "-"),
            structured_data=str(structured_data or {}),
            retrieved_passages=passages_text,
        )

        response = await model.generate_content_async(
            contents=[prompt, f"Farmer question: {question}"]
        )
        return response.text.strip()
    except Exception as exc:
        logger.warning("Gemini generation failed (%s). Falling back to direct passages.", exc)
        # Direct fallback rule
        if language == "en":
            return f"Service notice: Showing retrieved reference directly:\n\n{passages_text}"
        return f"प्रामाणिक संदर्भ विवरण:\n\n{passages_text}"
