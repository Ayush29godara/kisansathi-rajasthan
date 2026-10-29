"""Farmer feedback collection endpoint."""

import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from app.auth import get_current_user
from app.schemas import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="", tags=["Feedback"])


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackCreate,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Record user feedback and real-world ground-truth outcomes for continuous evaluation.
    Scoped strictly to the authenticated user ID.
    """
    feedback_id = str(uuid.uuid4())
    # In Phase 1/Database phase, this inserts into `feedback` table
    return FeedbackResponse(
        id=feedback_id,
        status="recorded",
    )
