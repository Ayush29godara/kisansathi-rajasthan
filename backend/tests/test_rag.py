"""Unit tests for RAG knowledge retrieval and LLM language synthesis."""

import pytest
from app.schemas import SourceCitation
from services.rag import retrieve_relevant_chunks
from services.llm import generate_grounded_answer
from services.intent import classify_intent


@pytest.mark.asyncio
async def test_retrieve_relevant_chunks_in_test_mode():
    """Ensure RAG retrieval returns curated Rajasthan agriculture citations in test mode."""
    citations = await retrieve_relevant_chunks("सरसों की बुवाई")
    assert isinstance(citations, list)
    assert len(citations) > 0
    assert "ICAR" in citations[0].source or "Rajasthan" in citations[0].doc_title
    assert citations[0].relevance_score is not None


@pytest.mark.asyncio
async def test_retrieve_relevant_chunks_respects_limit():
    """Ensure RAG retrieval respects the requested max limit."""
    citations = await retrieve_relevant_chunks("बाजरा", limit=1)
    assert len(citations) <= 1


@pytest.mark.asyncio
async def test_llm_answer_no_sources_invokes_kvk_fallback():
    """When no sources are retrieved, LLM must refuse to invent and refer to KVK."""
    answer_hi = await generate_grounded_answer(
        question="मंगल ग्रह पर धान कैसे उगाएं?",
        sources=[],
        language="hi",
    )
    assert "कृषि विज्ञान केंद्र" in answer_hi or "KVK" in answer_hi

    answer_en = await generate_grounded_answer(
        question="How to grow rice on Mars?",
        sources=[],
        language="en",
    )
    assert "KVK" in answer_en or "Krishi Vigyan Kendra" in answer_en


@pytest.mark.asyncio
async def test_llm_answer_in_test_mode_presents_retrieved_passages():
    """In test mode or when unassisted, LLM surfaces authentic passages directly."""
    sample_citation = SourceCitation(
        doc_title="Rajasthan Rabi Crop Guide",
        source="SKRAU Bikaner",
        chunk_text="सरसों में तना सड़न रोग रोकथाम हेतु कार्बेन्डाजिम से बीज उपचार करें।",
        relevance_score=0.91,
    )
    answer = await generate_grounded_answer(
        question="सरसों के तना सड़न का इलाज?",
        sources=[sample_citation],
        language="hi",
    )
    assert "SKRAU Bikaner" in answer or "सत्यापित" in answer or "प्रामाणिक" in answer
    assert "कार्बेन्डाजिम" in answer


def test_intent_classification_precedence():
    """Ensure technical domain intents take precedence over general conversation."""
    assert classify_intent("नमस्ते, सरसों में रोग का उपचार बताएं") == "disease"
    assert classify_intent("गेहूं का मंडी भाव और रेट क्या है?") == "price"
    assert classify_intent("बाजरे का उत्पादन और उपज का अनुमान") == "yield"
    assert classify_intent("कल मौसम कैसा रहेगा और बारिश कब होगी?") == "weather"
    assert classify_intent("नमस्ते किसान साथी") == "general"
    assert classify_intent("   ") == "general"
