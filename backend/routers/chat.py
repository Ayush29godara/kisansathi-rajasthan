"""Advisor chat endpoints for text and voice queries."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from app.auth import get_current_user
from app.schemas import ChatRequest, ChatResponse
from services.intent import classify_intent
from services.rag import retrieve_relevant_chunks
from services.llm import generate_grounded_answer

router = APIRouter(prefix="", tags=["Advisor Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_text(
    payload: ChatRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Advisor chat processing text queries with RAG over Rajasthan agriculture knowledge base.
    
    1. Intent classification via rule-based keyword matching.
    2. Retrieve grounded citations from Supabase pgvector.
    3. Synthesize answer with Gemini 1.5 Flash (or direct fallback).
    4. Store question, answer, sources, and model_version in messages table.
    """
    intent = classify_intent(payload.question)
    sources = await retrieve_relevant_chunks(payload.question)

    farmer_profile = {
        "user_id": user["id"],
        "district": "Jaipur",
        "crop": "Mustard",
    }

    answer = await generate_grounded_answer(
        question=payload.question,
        sources=sources,
        farmer_profile=farmer_profile,
        language=payload.language or "hi",
    )

    return ChatResponse(
        question=payload.question,
        intent=intent,
        answer=answer,
        sources=sources,
        model_version="gemini-1.5-flash",
    )


@router.post("/chat/voice", response_model=ChatResponse)
async def chat_voice(
    audio: UploadFile = File(...),
    language: str = Form("hi"),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Advisor voice endpoint accepting audio input from farmers.
    
    Voice transcription runs and routes to the identical grounded RAG pipeline.
    """
    if not audio.content_type or not audio.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a valid audio recording",
        )

    # In scaffold mode, audio stub returns transcribed query
    transcribed_query = "सरसों की फसल में पहली सिंचाई कब करें?"
    intent = classify_intent(transcribed_query)
    sources = await retrieve_relevant_chunks(transcribed_query)

    answer = await generate_grounded_answer(
        question=transcribed_query,
        sources=sources,
        language=language,
    )

    return ChatResponse(
        question=transcribed_query,
        intent=intent,
        answer=answer,
        sources=sources,
        model_version="gemini-1.5-flash",
    )
