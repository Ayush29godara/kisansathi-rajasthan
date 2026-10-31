"""Retrieval-Augmented Generation (RAG) knowledge base service over Supabase pgvector.

Combines verified Rajasthan Agriculture Universities (AU Kota, SKNAU Jobner, SKRAU Bikaner)
and ICAR institutes (DRMR Bharatpur, CAZRI Jodhpur, IIWBR Karnal) Packages of Practices (POP)
with Supabase pgvector vector search for authentic, grounded agricultural advisory.
"""

import hashlib
import logging
import re
from collections import OrderedDict
from typing import List, Optional, Dict, Any

import httpx

from app.config import get_settings
from app.schemas import SourceCitation
from services.disease_service import VERIFIED_DISEASE_KB

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EMBEDDING_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent"
)

# ---------------------------------------------------------------------------
# Module-level embedding cache (LRU, max 100 entries)
# ---------------------------------------------------------------------------
_embedding_cache: OrderedDict[str, List[float]] = OrderedDict()
_EMBEDDING_CACHE_MAX = 100


def _cache_key(text: str) -> str:
    """Return a deterministic hash key for embedding cache lookups."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _put_cache(key: str, value: List[float]) -> None:
    """Insert into LRU cache, evicting oldest if over capacity."""
    _embedding_cache[key] = value
    _embedding_cache.move_to_end(key)
    while len(_embedding_cache) > _EMBEDDING_CACHE_MAX:
        _embedding_cache.popitem(last=False)


# ---------------------------------------------------------------------------
# Fallback citations for test / offline mode
# ---------------------------------------------------------------------------
_FALLBACK_CITATIONS: List[SourceCitation] = [
    SourceCitation(
        doc_title="ICAR Package of Practices for Rajasthan",
        source="ICAR-CAZRI Jodhpur / Agriculture University Kota",
        chunk_text=(
            "राजस्थान में सरसों और बाजरा की उन्नत किस्मों, संतुलित उर्वरक (NPK) एवं "
            "सामयिक सिंचाई प्रबंधन से फसल की उत्पादकता 20-30% तक बढ़ाई जा सकती है। "
            "रोग नियंत्रण हेतु केवल अनुशंसित मात्रा में ही जैव या रासायनिक उपचार करें।"
        ),
        relevance_score=0.88,
    ),
    SourceCitation(
        doc_title="KVK Rajasthan Advisory Bulletin",
        source="Krishi Vigyan Kendra, Jaipur",
        chunk_text=(
            "सरसों में सफेद रोली (White Rust) रोग के लक्षण दिखने पर "
            "Mancozeb 75 WP @ 2.5 ग्राम/लीटर पानी में घोलकर छिड़काव करें। "
            "दूसरा छिड़काव 15 दिन बाद करें। बीज उपचार Metalaxyl से करें।"
        ),
        relevance_score=0.82,
    ),
]


# ---------------------------------------------------------------------------
# Verified Rajasthan Agronomy Knowledge (University POPs)
# ---------------------------------------------------------------------------
_VERIFIED_AGRONOMY_KB: List[Dict[str, Any]] = [
    {
        "id": "wheat_agronomy",
        "crop": "Wheat",
        "doc_title": "Package of Practices for Wheat in Rajasthan",
        "source": "Agriculture University Kota / ICAR-IIWBR Karnal",
        "keywords": ["wheat", "gehu", "gehun", "गेहूं", "गेंहू", "बुवाई", "buwai", "buai", "bowai", "kab", "when", "urea", "khad", "सिंचाई", "खाद", "यूरिया", "sowing", "irrigation", "fertilizer", "urea", "seed rate", "विटावैक्स", "खरपतवार"],
        "chunk_text": (
            "गेहूं की समय पर बुवाई 1 से 15 नवंबर तक करें। बीज दर 100 किग्रा प्रति हेक्टेयर रखें (देर से बुवाई में 125 किग्रा)। "
            "बीज उपचार कार्बोक्सिन + थीरम (विटावैक्स 75 WP) 2.5 ग्राम प्रति किग्रा बीज से करें। "
            "उर्वरक प्रबंधन: 120 किग्रा नाइट्रोजन, 60 किग्रा फास्फोरस व 40 किग्रा पोटाश प्रति हेक्टेयर। "
            "आधी नाइट्रोजन व पूरी फास्फोरस-पोटाश बुवाई पर, शेष नाइट्रोजन पहली व दूसरी सिंचाई पर दें। "
            "सिंचाई की सबसे क्रांतिक अवस्था बुवाई के 20-25 दिन बाद मुकुट जड़ (CRI) निकलना है। "
            "खरपतवार नियंत्रण हेतु चौड़ी पत्ती वाले खरपतवारों के लिए 2,4-D (38% EC) 1.25 लीटर/हेक्टेयर तथा मंडूसी/गुल्ली डंडा हेतु क्लोडिनाफॉप 400 ग्राम/हेक्टेयर बुवाई के 30-35 दिन बाद छिड़कें।"
        ),
    },
    {
        "id": "mustard_agronomy",
        "crop": "Mustard",
        "doc_title": "Package of Practices for Rapeseed-Mustard",
        "source": "ICAR-Directorate of Rapeseed-Mustard Research (DRMR), Bharatpur",
        "keywords": ["mustard", "सरसों", "राई", "sarson", "sarso", "बुवाई", "buwai", "buai", "bowai", "kab", "when", "khad", "सिंचाई", "गंधक", "सल्फर", "irrigation", "sulfur", "fertilizer", "urea"],
        "chunk_text": (
            "सरसों की बुवाई 1 से 20 अक्टूबर के मध्य करें। बीज दर 4 से 5 किग्रा प्रति हेक्टेयर। "
            "कतार से कतार की दूरी 30-45 सेमी व पौधे से पौधा 10-15 सेमी रखें। "
            "उर्वरक: 80 किग्रा नाइट्रोजन, 40 किग्रा फास्फोरस व 40 किग्रा गंधक (सल्फर) प्रति हेक्टेयर। "
            "सरसों में गंधक (जिप्सम 250 किग्रा या बेंटोनाइट सल्फर 25 किग्रा) तेल प्रतिशत और दाना भराव में अत्यंत लाभकारी है। "
            "सिंचाई: पहली सिंचाई फूल आने से पूर्व (30-35 दिन) तथा दूसरी सिंचाई फलियां बनते समय (60-65 दिन) करें।"
        ),
    },
    {
        "id": "gram_agronomy",
        "crop": "Gram",
        "doc_title": "Package of Practices for Gram (Chickpea) in Rajasthan",
        "source": "Rajasthan State Agricultural Universities - Package of Practices (summary)",
        "keywords": ["gram", "chana", "चना", "chickpea", "बुवाई", "buwai", "bowai", "sowing", "kab", "when", "seed rate", "बीज दर"],
        "chunk_text": (
            "चने की बुवाई असिंचित क्षेत्रों में अक्टूबर के दूसरे पखवाड़े तथा सिंचित क्षेत्रों में अक्टूबर अंत से नवंबर के पहले सप्ताह तक करें। "
            "बीज दर 75-80 किग्रा प्रति हेक्टेयर। बीज को राइजोबियम व फास्फोरस घुलनशील जीवाणु (PSB) कल्चर से उपचारित करें। "
            "चने में सामान्यतः 1-2 सिंचाई (शाखा निकलते समय व फली बनते समय) पर्याप्त होती है; फूल आते समय सिंचाई न करें।"
        ),
    },
    {
        "id": "soybean_guar_agronomy",
        "crop": "Soybean",
        "doc_title": "Package of Practices for Kharif Soybean and Guar",
        "source": "Agriculture University Kota / SKRAU Bikaner - Package of Practices (summary)",
        "keywords": ["soybean", "सोयाबीन", "guar", "ग्वार", "बुवाई", "buwai", "bowai", "sowing", "kab", "when", "seed rate", "बीज दर"],
        "chunk_text": (
            "सोयाबीन की बुवाई मानसून की पर्याप्त वर्षा के बाद 20 जून से 10 जुलाई के बीच करें; बीज दर 75-80 किग्रा प्रति हेक्टेयर। "
            "ग्वार की बुवाई जुलाई के प्रथम पखवाड़े में वर्षा होने पर करें; बीज दर 15-20 किग्रा प्रति हेक्टेयर। "
            "दोनों फसलों में बीज को राइजोबियम कल्चर से उपचारित कर बोएं तथा खेत में जल निकास की उचित व्यवस्था रखें।"
        ),
    },
    {
        "id": "frost_protection_rajasthan",
        "crop": "All",
        "doc_title": "Advisory for Cold Wave and Frost Protection in Rajasthan",
        "source": "Rajasthan Directorate of Agriculture & AU Kota",
        "keywords": ["frost", "cold", "पाला", "ठंड", "शीतलहर", "freezing", "temperature", "तापमान"],
        "chunk_text": (
            "राजस्थान में दिसंबर-जनवरी में तापमान 4°C से नीचे जाने पर पाला (Frost) का खतरा रहता है। "
            "सरसों, चना, टमाटर व आलू पाले से सबसे ज्यादा प्रभावित होते हैं। "
            "पाले से बचाव के उपाय: 1. पाले की संभावना होने पर खेत में शाम को हल्की सिंचाई करें। "
            "2. 0.1% गंधक का तेजाब (कमर्शियल सल्फ्यूरिक एसिड 1 मिली प्रति लीटर पानी) का फसल पर छिड़काव करें। "
            "3. खेत की उत्तरी-पश्चिमी दिशा में शाम को कूड़ा-कचरा जलाकर धुआं करें ताकि खेत का तापमान बढ़ सके।"
        ),
    },
    {
        "id": "bajra_agronomy",
        "crop": "Bajra",
        "doc_title": "Package of Practices for Kharif Pearl Millet",
        "source": "ICAR - Central Arid Zone Research Institute (CAZRI), Jodhpur",
        "keywords": ["bajra", "bajre", "बाजरा", "millet", "pearl millet", "बुवाई", "buwai", "buai", "bowai", "kab", "when", "sowing", "khad", "खाद", "उर्वरक", "एट्राजीन", "varieties"],
        "chunk_text": (
            "बाजरा की बुवाई मानसून की पहली अच्छी वर्षा (जुलाई प्रथम पखवाड़ा) में करें। बीज दर 4-5 किग्रा/हेक्टेयर। "
            "उन्नत संकर किस्में: MPMH-17, HHB-67 सुधरी, RHB-177। "
            "उर्वरक: 60 किग्रा नाइट्रोजन व 30 किग्रा फास्फोरस प्रति हेक्टेयर। "
            "खरपतवार नियंत्रण हेतु बुवाई के 48 घंटे के भीतर एट्राजीन 50% WP @ 1 किग्रा/हेक्टेयर 500 लीटर पानी में घोलकर छिड़कें। "
            "बाजरे में कल्ले फूटते समय व बाली निकलते समय नमी बनाए रखना आवश्यक है।"
        ),
    },
    {
        "id": "tomato_agronomy",
        "crop": "Tomato",
        "doc_title": "Vegetable Production & Nutrient Guide for Rajasthan",
        "source": "Sri Karan Narendra Agriculture University (SKNAU), Jobner",
        "keywords": ["tomato", "टमाटर", "नर्सरी", "खाद", "सिंचाई", "पीला", "yellow", "nursery", "drip", "mulch"],
        "chunk_text": (
            "टमाटर की रबी फसल हेतु पौध अक्टूबर-नवंबर में खेत में लगाएं। "
            "नर्सरी में सफेद मक्खी से बचाव हेतु 40-मेष की कीटरोधी जाली का प्रयोग करें। "
            "उर्वरक: 120-150 किग्रा नाइट्रोजन, 80 किग्रा फास्फोरस व 60 किग्रा पोटाश प्रति हेक्टेयर। "
            "पत्तियों के पीलेपन व पोषक तत्व कमी में जिंक सल्फेट (21%) 5 ग्राम + चूना 2.5 ग्राम प्रति लीटर पानी का छिड़काव करें। "
            "ड्रिप सिंचाई व प्लास्टिक मल्चिंग से 40% पानी की बचत एवं गुणवत्तापूर्ण उत्पादन मिलता है।"
        ),
    },
    {
        "id": "micronutrient_deficiency_rajasthan",
        "crop": "All",
        "doc_title": "Micronutrient Management in Rajasthan Soils",
        "source": "ICAR-CAZRI & SKRAU Bikaner",
        "keywords": ["zinc", "iron", "जिंक", "लोहा", "पत्तियां पीली", "yellowing", "deficiency", "खैरा", "chlorosis", "पोषक तत्व"],
        "chunk_text": (
            "राजस्थान की रेतीली एवं चूनेदार मिट्टी में जस्ता (Zinc) और लोहा (Iron) की कमी प्रमुखता से पाई जाती है। "
            "जिंक की कमी से नई पत्तियां छोटी व पीली पड़ती हैं। उपचार: 25 किग्रा जिंक सल्फेट प्रति हेक्टेयर बुवाई पर दें "
            "अथवा 0.5% जिंक सल्फेट (5 ग्राम/लीटर) + 2.5 ग्राम बुझा चूना का छिड़काव करें। "
            "लोहे (Iron) की कमी से ऊपरी नई पत्तियां पीली व नसें हरी दिखती हैं। इसके लिए 0.5% फेरस सल्फेट (5 ग्राम/लीटर) + 0.5 ग्राम सिट्रिक एसिड का छिड़काव करें।"
        ),
    },
]


def _match_verified_agronomy_kb(query: str, crop: Optional[str] = None) -> List[SourceCitation]:
    """
    Search curated university Package of Practices and Disease KB for authoritative advice.
    """
    q = query.lower()
    citations: List[SourceCitation] = []

    # 1. Match against VERIFIED_DISEASE_KB
    for key, item in VERIFIED_DISEASE_KB.items():
        score = 0.0
        item_crop = item.get("crop", "").lower()
        if crop and crop.lower() == item_crop:
            score += 0.35
        elif item_crop and item_crop in q:
            score += 0.35

        d_name = item.get("disease_name", "").lower()
        treatment = item.get("treatment", "").lower()
        prevention_text = " ".join(item.get("prevention", [])).lower()

        # Keyword matching
        for word in re.findall(r"\w{3,}", q):
            if word in d_name or word in key:
                score += 0.25
            elif word in treatment or word in prevention_text:
                score += 0.15

        # Symptom specific boosting
        if any(w in q for w in ["yellow", "पीला", "पीली"]):
            if any(w in key for w in ["yellow", "curl", "rust", "mosaic", "blight"]):
                score += 0.35
        if any(w in q for w in ["spot", "spots", "धब्बा", "धब्बे", "चित्ती"]):
            if any(w in key for w in ["spot", "blight", "rust", "leaf"]):
                score += 0.30
        if any(w in q for w in ["white rust", "सफेद रोली", "रोली"]):
            if "white_rust" in key or "rust" in key:
                score += 0.50
        if any(w in q for w in ["aphid", "chepa", "चेपा", "माहू", "मोयला"]):
            if "aphid" in key:
                score += 0.50
        if any(w in q for w in ["rot", "smut", "कंडवा", "सड़न"]):
            if any(w in key for w in ["smut", "rot"]):
                score += 0.40

        if score >= 0.50:
            chunk_body = (
                f"रोग / समस्या: {item['disease_name']}\n"
                f"अनुशंसित उपचार: {item['treatment']}\n"
                f"रोकथाम व प्रबंधन: {' '.join(item.get('prevention', []))}"
            )
            citations.append(
                SourceCitation(
                    doc_title=item["disease_name"],
                    source=item["source"],
                    chunk_text=chunk_body,
                    relevance_score=min(round(score, 2), 0.98),
                )
            )

    # 2. Match against _VERIFIED_AGRONOMY_KB
    for item in _VERIFIED_AGRONOMY_KB:
        score = 0.0
        item_crop = item.get("crop", "").lower()
        if crop and crop.lower() == item_crop:
            score += 0.30
        elif item_crop != "all" and item_crop in q:
            score += 0.30

        for kw in item["keywords"]:
            if kw.lower() in q:
                score += 0.25

        if score >= 0.50:
            citations.append(
                SourceCitation(
                    doc_title=item["doc_title"],
                    source=item["source"],
                    chunk_text=item["chunk_text"],
                    relevance_score=min(round(score, 2), 0.96),
                )
            )

    citations.sort(key=lambda c: c.relevance_score or 0.0, reverse=True)
    return citations


# ---------------------------------------------------------------------------
# Embedding helper
# ---------------------------------------------------------------------------

async def _embed_query(query: str) -> Optional[List[float]]:
    """
    Embed a query string using the Gemini embedding-001 REST API.

    Uses module-level LRU cache to avoid redundant API calls.
    Returns None on failure.
    """
    key = _cache_key(query)
    if key in _embedding_cache:
        _embedding_cache.move_to_end(key)
        return _embedding_cache[key]

    payload = {
        "content": {"parts": [{"text": query}]},
        "outputDimensionality": 768,
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                EMBEDDING_ENDPOINT,
                json=payload,
                headers={"x-goog-api-key": settings.GEMINI_API_KEY},
                timeout=15.0,
            )
            resp.raise_for_status()
            values = resp.json()["embedding"]["values"]
            _put_cache(key, values)
            return values
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Embedding API HTTP %d: %s",
            exc.response.status_code,
            exc.response.text[:300],
        )
        return None
    except Exception as exc:
        logger.error("Embedding request failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Main retrieval function
# ---------------------------------------------------------------------------

async def retrieve_relevant_chunks(
    query: str,
    crop: Optional[str] = None,
    limit: int = 4,
    min_similarity: float = 0.35,
) -> List[SourceCitation]:
    """
    Retrieve the most relevant knowledge-base chunks for a farmer query.

    Pipeline:
        1. Query curated Rajasthan Agriculture University & ICAR verified POP guidelines.
        2. Embed query and call Supabase RPC match_kb_chunks for vector similarity.
        3. Merge, deduplicate, and return top authentic citations.
    """
    # ---- Test mode: return deterministic fallbacks ----
    if settings.ENVIRONMENT == "test":
        return _FALLBACK_CITATIONS[:limit]

    # ---- Guard: empty query ----
    if not query or not query.strip():
        logger.warning("Empty query received — returning no results.")
        return []

    # 1. First search verified university POP and disease guidelines
    curated_citations = _match_verified_agronomy_kb(query, crop=crop)

    # 2. Search Supabase vector store if credentials are present
    vector_citations: List[SourceCitation] = []
    if settings.GEMINI_API_KEY and settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        try:
            embedding = await _embed_query(query)
            if embedding:
                rpc_url = f"{settings.SUPABASE_URL}/rest/v1/rpc/match_kb_chunks"
                headers = {
                    "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                    "Content-Type": "application/json",
                }
                rpc_payload = {
                    "query_embedding": embedding,
                    "match_threshold": min_similarity,
                    "match_count": limit * 2,
                }
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        rpc_url,
                        json=rpc_payload,
                        headers=headers,
                        timeout=10.0,
                    )
                    if resp.status_code == 200:
                        rows = resp.json()
                        for row in rows:
                            text = row.get("chunk_text") or ""
                            # Filter out unreadable KrutiDev ASCII glyph corruption
                            if "fd;k tk" in text or "djsa" in text or "vLr" in text:
                                continue
                            if crop:
                                crop_lower = crop.lower()
                                if (
                                    crop_lower not in (row.get("doc_title") or "").lower()
                                    and crop_lower not in text.lower()
                                ):
                                    continue
                            vector_citations.append(
                                SourceCitation(
                                    doc_title=row.get("doc_title", "Unknown"),
                                    source=row.get("source", "Unknown"),
                                    chunk_text=text,
                                    relevance_score=row.get("similarity"),
                                )
                            )
        except Exception as exc:
            logger.warning("Supabase vector retrieval encountered an issue: %s", exc)

    # 3. Merge citations with priority to curated university data
    all_citations = curated_citations + vector_citations
    
    # Deduplicate by doc_title
    seen_titles = set()
    deduped: List[SourceCitation] = []
    for c in all_citations:
        if c.doc_title not in seen_titles:
            seen_titles.add(c.doc_title)
            deduped.append(c)

    deduped.sort(key=lambda c: c.relevance_score or 0.0, reverse=True)
    return deduped[:limit]
