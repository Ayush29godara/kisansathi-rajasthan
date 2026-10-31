"""Advisor chat endpoints for text and voice queries with RAG knowledge grounding."""

import re
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.config import get_settings
from app.demo_store import is_demo_user, get_demo_farm
from app.models import FarmModel, MessageModel, FeedbackModel
from app.schemas import ChatRequest, ChatResponse, HistoryItemResponse
from app.rate_limiter import check_chat_rate_limit
from services.intent import classify_intent
from services.rag import retrieve_relevant_chunks
from services.llm import generate_grounded_answer
from services.chat_context import build_structured_context

logger = logging.getLogger("kisansathi.chat")
settings = get_settings()

router = APIRouter(prefix="", tags=["Advisor Chat"])

# In-memory store for demo farmer chat history
_demo_chat_history: Dict[str, List[Dict[str, Any]]] = {}


def detect_crop_from_query(query: str) -> Optional[str]:
    """
    Extract crop mentioned in user query, prioritizing explicit farmer intent.
    If a farmer asking a question about 'tomato' has 'mustard' in their profile,
    the tomato query takes precedence for retrieval.
    """
    q = query.lower()
    crop_keywords = [
        ("Tomato", ["tomato", "टमाटर"]),
        ("Wheat", ["wheat", "गेहूं", "गेंहू", "गेहू"]),
        ("Mustard", ["mustard", "सरसों", "राई", "sarson", "sarso"]),
        ("Bajra", ["bajra", "बाजरा", "pearl millet", "millet"]),
        ("Soybean", ["soybean", "सोयाबीन", "soya"]),
        ("Guar", ["guar", "ग्वार", "cluster bean"]),
        ("Gram", ["gram", "chana", "चना", "छोला"]),
        ("Cotton", ["cotton", "कपास", "नरमा"]),
        ("Onion", ["onion", "प्याज", "कांदा"]),
        ("Garlic", ["garlic", "लहसुन"]),
        ("Cumin", ["cumin", "जीरा", "jeera"]),
        ("Coriander", ["coriander", "धनिया"]),
        ("Fenugreek", ["fenugreek", "मेथी"]),
        ("Moong", ["moong", "मूंग", "green gram"]),
        ("Moth", ["moth", "मोठ", "moth bean"]),
        ("Groundnut", ["groundnut", "मूंगफली", "peanut"]),
    ]
    for crop_name, keywords in crop_keywords:
        for kw in keywords:
            if kw.isascii():
                # Whole-word match so "kilogram"/"program" do not trigger "gram", "mother" not "moth"
                if re.search(rf"\b{re.escape(kw)}(?:s|es)?\b", q):
                    return crop_name
            elif kw in q:
                return crop_name
    return None


def _get_farmer_context(user_id: str, db: Optional[Session]) -> Dict[str, Any]:
    """Retrieve personalized farm profile context if available."""
    context: Dict[str, Any] = {
        "user_id": user_id,
        "district": "Rajasthan",
        "tehsil": "-",
        "crop": "-",
        "land_hectare": "-",
        "irrigation": "-",
        "sowing_date": "-",
    }
    # Demo sessions use the in-memory demo store so edited farm details are honoured
    if is_demo_user(user_id):
        farm = get_demo_farm(user_id)
        context.update({
            "district": farm["district"],
            "tehsil": farm["tehsil"],
            "crop": farm["crop"],
            "land_hectare": float(farm["land_hectare"]),
            "irrigation": farm["irrigation"],
            "sowing_date": str(farm["sowing_date"]),
        })
        return context

    if db is None:
        return context

    try:
        farm = (
            db.query(FarmModel)
            .filter(FarmModel.user_id == user_id)
            .order_by(FarmModel.updated_at.desc())
            .first()
        )
        if farm:
            context.update({
                "district": farm.district,
                "tehsil": farm.tehsil,
                "crop": farm.crop,
                "land_hectare": float(farm.land_hectare),
                "irrigation": farm.irrigation,
                "sowing_date": str(farm.sowing_date),
            })
    except Exception as exc:
        if db:
            db.rollback()
        logger.warning("Could not load farm profile for user %s: %s", user_id, exc)

    return context


def _save_message(
    message_id: str,
    user_id: str,
    question: str,
    intent: str,
    answer: str,
    sources: list,
    model_version: str,
    db: Optional[Session],
) -> None:
    """Persist chat query and grounded response to database (or demo cache)."""
    serialized_sources = [s.model_dump() if hasattr(s, "model_dump") else s for s in sources]

    # Store in memory for demo farmer sessions
    if user_id.startswith("demo-"):
        if user_id not in _demo_chat_history:
            _demo_chat_history[user_id] = []
        _demo_chat_history[user_id].insert(0, {
            "id": message_id,
            "user_id": user_id,
            "question": question,
            "intent": intent,
            "answer": answer,
            "sources": serialized_sources,
            "model_version": model_version,
            "created_at": datetime.now(timezone.utc),
        })

    if db is None:
        return

    # In PostgreSQL, demo farmers are not in auth.users, so skip database FK insertion
    if user_id.startswith("demo-") and settings.ENVIRONMENT != "test":
        return

    try:
        record = MessageModel(
            id=message_id,
            user_id=user_id,
            question=question,
            intent=intent,
            answer=answer,
            sources=serialized_sources,
            model_version=model_version,
        )
        db.add(record)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("Failed to store message log: %s", exc)


async def _answer_question(
    question: str,
    language: str,
    user_id: str,
    farmer_profile: Dict[str, Any],
    db: Optional[Session],
):
    """Shared pipeline for text and voice chat: intent, live data, RAG retrieval, LLM synthesis."""
    intent = classify_intent(question)

    # Detect crop: the crop named in the question takes precedence over the profile crop
    detected_crop = detect_crop_from_query(question)
    active_profile = dict(farmer_profile)
    if detected_crop:
        active_profile["crop"] = detected_crop
    crop_filter = active_profile.get("crop") if active_profile.get("crop") != "-" else None

    # Live structured data (mandi prices, weather/irrigation, yield) for matching intents
    structured_data, live_sources = await build_structured_context(
        intent=intent,
        question=question,
        profile=farmer_profile,
        detected_crop=detected_crop,
        language=language,
        db=db,
    )

    # Grounded RAG retrieval
    kb_sources = await retrieve_relevant_chunks(
        query=question,
        crop=crop_filter,
        limit=4,
    )
    sources = (live_sources + kb_sources)[:5]

    answer = await generate_grounded_answer(
        question=question,
        sources=sources,
        farmer_profile=active_profile,
        structured_data=structured_data or None,
        language=language,
    )
    return intent, answer, sources


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(check_chat_rate_limit)])
async def chat_text(
    payload: ChatRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """
    Advisor chat processing text queries with RAG over Rajasthan agriculture knowledge base.

    1. Classify intent via rule-based keyword matching.
    2. Extract crop from query (e.g. Tomato or Wheat), falling back to farmer profile crop.
    3. Retrieve relevant chunks from university POPs and pgvector vector search.
    4. Synthesize answer with Gemini grounded strictly in retrieved sources.
    5. Store question, answer, sources, and model_version in messages table.
    """
    user_id = str(user["id"])
    farmer_profile = _get_farmer_context(user_id, db)

    intent, answer, sources = await _answer_question(
        question=payload.question,
        language=payload.language or "hi",
        user_id=user_id,
        farmer_profile=farmer_profile,
        db=db,
    )

    message_id = str(uuid.uuid4())
    model_version = "gemini-1.5-flash" if settings.ENVIRONMENT == "test" else (getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite") or "gemini-3.5-flash-lite")

    # Persist interaction history
    _save_message(
        message_id=message_id,
        user_id=user_id,
        question=payload.question,
        intent=intent,
        answer=answer,
        sources=sources,
        model_version=model_version,
        db=db,
    )

    return ChatResponse(
        id=message_id,
        question=payload.question,
        intent=intent,
        answer=answer,
        sources=sources,
        model_version=model_version,
    )


@router.post("/chat/voice", response_model=ChatResponse, dependencies=[Depends(check_chat_rate_limit)])
async def chat_voice(
    audio: UploadFile = File(...),
    transcript: Optional[str] = Form(None),
    language: str = Form("hi"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """
    Advisor voice endpoint accepting audio input from farmers.
    Accepts an audio file and an optional client-side transcript (from Web Speech API).
    Routes query through identical grounded RAG pipeline.
    """
    if not audio.content_type or not audio.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a valid audio recording (audio/* MIME type required)",
        )

    # Use client-side transcript if supplied, or default query for testing/stub
    query_text = (transcript or "").strip()
    if not query_text:
        query_text = (
            "सरसों की फसल में पहली सिंचाई कब करें?"
            if language == "hi"
            else "When should the first irrigation be done for mustard?"
        )

    user_id = str(user["id"])
    farmer_profile = _get_farmer_context(user_id, db)

    intent, answer, sources = await _answer_question(
        question=query_text,
        language=language,
        user_id=user_id,
        farmer_profile=farmer_profile,
        db=db,
    )

    message_id = str(uuid.uuid4())
    model_version = "gemini-1.5-flash" if settings.ENVIRONMENT == "test" else (getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite") or "gemini-3.5-flash-lite")

    _save_message(
        message_id=message_id,
        user_id=user_id,
        question=query_text,
        intent=intent,
        answer=answer,
        sources=sources,
        model_version=model_version,
        db=db,
    )

    return ChatResponse(
        id=message_id,
        question=query_text,
        intent=intent,
        answer=answer,
        sources=sources,
        model_version=model_version,
    )


@router.get("/history", response_model=List[HistoryItemResponse], tags=["Advisor Chat"])
async def get_chat_history(
    limit: int = 50,
    offset: int = 0,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """
    Retrieve historical queries and AI advisory responses for the authenticated farmer.
    Includes model_version and user feedback if provided.
    """
    user_id = str(user["id"])

    # If demo farmer, serve from demo history
    if user_id.startswith("demo-"):
        demo_items = _demo_chat_history.get(user_id, [])[offset : offset + limit]
        return [
            HistoryItemResponse(
                id=m["id"],
                question=m["question"],
                intent=m["intent"],
                answer=m["answer"],
                sources=m["sources"],
                model_version=m["model_version"],
                created_at=m["created_at"],
                feedback_rating=None,
                actual_outcome=None,
            )
            for m in demo_items
        ]

    if db is None:
        return []

    try:
        messages = (
            db.query(MessageModel)
            .filter(MessageModel.user_id == user_id)
            .order_by(MessageModel.created_at.desc())
            .offset(offset)
            .limit(min(limit, 100))
            .all()
        )

        # Batch lookup feedback for these messages
        msg_ids = [m.id for m in messages]
        feedback_map: Dict[str, FeedbackModel] = {}
        if msg_ids:
            feedbacks = (
                db.query(FeedbackModel)
                .filter(FeedbackModel.message_id.in_(msg_ids))
                .all()
            )
            for fb in feedbacks:
                feedback_map[str(fb.message_id)] = fb

        results: List[HistoryItemResponse] = []
        for m in messages:
            fb = feedback_map.get(str(m.id))
            results.append(
                HistoryItemResponse(
                    id=str(m.id),
                    question=m.question,
                    intent=m.intent,
                    answer=m.answer,
                    sources=m.sources if isinstance(m.sources, list) else [],
                    model_version=m.model_version,
                    created_at=m.created_at,
                    feedback_rating=fb.rating if fb else None,
                    actual_outcome=fb.actual_outcome if fb else None,
                )
            )
        return results

    except Exception as exc:
        if db:
            db.rollback()
        logger.error("Error loading chat history for user %s: %s", user_id, exc)
        return []
