"""District yield prediction and driver attribution endpoints."""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.demo_store import is_demo_user, get_demo_farm
from app.models import FarmModel
from app.schemas import YieldOutlookResponse
from services.yield_service import get_district_yield_outlook

logger = logging.getLogger("kisansathi.yield_router")

router = APIRouter(prefix="", tags=["Yield Outlook"])


@router.get("/predict/yield", response_model=YieldOutlookResponse)
async def predict_yield(
    district: Optional[str] = Query(None, description="District name in Rajasthan (optional if farm profile exists)"),
    crop: Optional[str] = Query(None, description="Crop name (optional if farm profile exists)"),
    season: str = Query("Rabi", description="Kharif or Rabi"),
    year: int = Query(2026, description="Crop forecast year"),
    language: str = Query("hi", description="Response language: hi or en"),
    user: Dict[str, Any] = Depends(get_current_user),
    db: Optional[Session] = Depends(get_db),
):
    """
    Produce district crop yield outlook and key drivers.

    1. Scoped to authenticated user. If district/crop are omitted, automatically
       loads the farmer's registered farm profile.
    2. Reports machine learning predictions (XGBoost/LightGBM) when real models are present.
    3. Transparently falls back to 5-year historical district mean, reporting model_version = 'baseline'.
    """
    target_district = district
    target_crop = crop

    # If parameters not provided in query, look up user's active farm profile
    if (not target_district or not target_crop) and is_demo_user(str(user["id"])):
        demo_farm = get_demo_farm(str(user["id"]))
        target_district = target_district or demo_farm["district"]
        target_crop = target_crop or demo_farm["crop"]
    if (not target_district or not target_crop) and db is not None:
        try:
            farm = (
                db.query(FarmModel)
                .filter(FarmModel.user_id == str(user["id"]))
                .order_by(FarmModel.updated_at.desc())
                .first()
            )
            if farm:
                target_district = target_district or farm.district
                target_crop = target_crop or farm.crop
        except Exception as exc:
            db.rollback()
            logger.warning("Could not auto-fill yield parameters from farm profile: %s", exc)

    # Defaults if still unspecified
    target_district = target_district or "Jaipur"
    target_crop = target_crop or "Mustard"

    try:
        return get_district_yield_outlook(
            district=target_district,
            crop=target_crop,
            season=season,
            forecast_year=year,
            language=language,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
