"""Crop disease diagnosis and treatment advice endpoints."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from app.auth import get_current_user
from app.schemas import DiseaseDiagnosisResponse, DiseaseRecordCreate
from services.disease_service import sanitize_and_strip_exif, get_disease_advice

router = APIRouter(prefix="", tags=["Disease Diagnosis"])

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB limit


@router.post("/diagnose", response_model=DiseaseDiagnosisResponse)
async def diagnose_image_fallback(
    crop: str = Form(...),
    opt_in_store: bool = Form(False),
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Server-side fallback disease diagnosis when client ONNX Runtime Web cannot execute.
    
    Security & Privacy Rules:
    - Enforces JPEG/PNG only.
    - Limits size to 5MB.
    - Strips all EXIF metadata.
    - By default does NOT store user photos; only stores when opt_in_store=True.
    - Predictions with low confidence fall back directly to KVK referral.
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
        _ = sanitize_and_strip_exif(content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image content: {str(exc)}",
        )

    # Server fallback prediction stub (Phase 3 connects to onnx model)
    predicted_label = "mustard_white_rust" if crop.lower() == "mustard" else "uncertain_or_unrecognized"
    confidence = 0.85 if crop.lower() == "mustard" else 0.45

    return get_disease_advice(crop=crop, predicted_label=predicted_label, confidence=confidence)


@router.post("/advice/disease", response_model=DiseaseDiagnosisResponse)
async def get_advice_for_prediction(
    payload: DiseaseRecordCreate,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Fetch verified treatment and prevention advice for predictions computed in-browser via ONNX Runtime Web.
    
    If browser prediction confidence < 0.70, returns safe KVK fallback advice.
    """
    return get_disease_advice(
        crop=payload.crop,
        predicted_label=payload.predicted_label,
        confidence=payload.confidence,
    )
