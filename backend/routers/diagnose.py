"""Crop disease diagnosis and treatment advice endpoints."""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import DiseasePredictionModel
from app.schemas import DiseaseDiagnosisResponse, DiseaseRecordCreate
from app.rate_limiter import check_diagnose_rate_limit
from services.disease_service import (
    sanitize_and_strip_exif,
    classify_image_with_vision,
    get_disease_advice_from_kb,
    store_photo_if_opted_in,
)

logger = logging.getLogger("kisansathi.diagnose_router")

router = APIRouter(prefix="", tags=["Disease Diagnosis"])

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB limit


@router.post("/diagnose", response_model=DiseaseDiagnosisResponse, dependencies=[Depends(check_diagnose_rate_limit)])
async def diagnose_image_fallback(
    crop: str = Form(...),
    opt_in_store: bool = Form(False),
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """
    Server-side fallback disease diagnosis using Gemini 1.5 Flash Vision.
    
    Security & Privacy Rules:
    - Enforces JPEG/PNG only.
    - Limits size to 5MB.
    - Strips all EXIF metadata.
    - Stores photos in private Supabase bucket ONLY when opt_in_store=True.
    - Predictions with low confidence (< 0.70) fall back directly to KVK referral.
    - Clearly labelled as lower-confidence fallback.
    """
    if file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG and PNG images are supported",
        )

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size exceeds the 5 MB limit",
        )

    try:
        # Validate image integrity and strip EXIF
        clean_bytes = sanitize_and_strip_exif(content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image content: {str(exc)}",
        )

    # 1. Run server vision classification
    predicted_label, confidence, _ = await classify_image_with_vision(
        image_bytes=clean_bytes,
        crop=crop,
    )

    # 2. Grounded treatment retrieval from KB
    response = get_disease_advice_from_kb(
        crop=crop,
        predicted_label=predicted_label,
        confidence=confidence,
        db=db,
    )

    # 3. Handle opt-in photo storage in private bucket
    image_storage_path = None
    if opt_in_store:
        try:
            image_storage_path = await store_photo_if_opted_in(
                image_bytes=clean_bytes,
                user_id=str(user["id"]),
                crop=crop,
                opt_in=True,
            )
            response.image_path = image_storage_path
        except Exception as exc:
            logger.warning("Could not store opt-in photo: %s", exc)

    # 4. Record to database history
    if db is not None:
        try:
            record = DiseasePredictionModel(
                user_id=str(user["id"]),
                crop=crop,
                predicted_label=response.predicted_label,
                confidence=response.confidence,
                model_version=response.model_version,
                image_path=image_storage_path,
            )
            db.add(record)
            db.commit()
        except Exception as exc:
            logger.warning("Could not record disease diagnosis to database: %s", exc)

    return response


@router.post("/advice/disease", response_model=DiseaseDiagnosisResponse)
async def get_advice_for_prediction(
    payload: DiseaseRecordCreate,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """
    Fetch verified treatment and prevention advice for predictions computed in-browser via ONNX Runtime Web.
    
    1. Treatment is retrieved strictly from verified KB sources (zero invented chemical doses).
    2. If in-browser confidence < 0.70, returns safe KVK expert referral notice.
    3. Records diagnosis to user history.
    """
    response = get_disease_advice_from_kb(
        crop=payload.crop,
        predicted_label=payload.predicted_label,
        confidence=payload.confidence,
        db=db,
    )

    if db is not None:
        try:
            record = DiseasePredictionModel(
                user_id=str(user["id"]),
                crop=payload.crop,
                predicted_label=response.predicted_label,
                confidence=response.confidence,
                model_version=payload.model_version,
                image_path=payload.image_path,
            )
            db.add(record)
            db.commit()
        except Exception as exc:
            logger.warning("Could not record in-browser disease diagnosis to history: %s", exc)

    return response
