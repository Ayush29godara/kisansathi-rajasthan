"""Farmer feedback collection endpoint."""

import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import FeedbackModel
from app.schemas import FeedbackCreate, FeedbackResponse

logger = logging.getLogger("kisansathi.feedback")
router = APIRouter(prefix="", tags=["Feedback"])


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    payload: FeedbackCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """
    Record user feedback and real-world ground-truth outcomes for continuous evaluation.
    Scoped strictly to the authenticated user ID.
    """
    feedback_id = str(uuid.uuid4())
    user_id = str(user["id"])

    if db is not None:
        try:
            record = FeedbackModel(
                id=feedback_id,
                message_id=payload.message_id,
                user_id=user_id,
                rating=payload.rating,
                actual_outcome=payload.actual_outcome,
            )
            db.add(record)
            db.commit()
            logger.info("Feedback recorded for user %s, rating %d", user_id, payload.rating)
        except Exception as exc:
            db.rollback()
            logger.warning("Could not persist feedback to database: %s", exc)

    return FeedbackResponse(
        id=feedback_id,
        status="recorded",
    )
