"""Weather alerts and FAO-56 irrigation advisory endpoints."""

import logging
from datetime import date, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user_optional
from app.db import get_db
from app.models import FarmModel
from app.schemas import IrrigationScheduleResponse
from services.weather_service import get_irrigation_advisory

logger = logging.getLogger("kisansathi.weather_router")

router = APIRouter(prefix="", tags=["Weather & Irrigation"])


@router.get("/advice/weather", response_model=IrrigationScheduleResponse)
async def get_weather_and_irrigation_advice(
    district: Optional[str] = Query(None, description="Rajasthan district name (e.g. Kota, Alwar, Jaipur)"),
    crop: Optional[str] = Query(None, description="Crop name (e.g. Mustard, Wheat, Bajra)"),
    sowing_date: Optional[date] = Query(None, description="Sowing date (YYYY-MM-DD)"),
    irrigation_type: str = Query("tubewell", description="canal/tubewell/well/drip/sprinkler/rainfed"),
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    db: Optional[Session] = Depends(get_db),
):
    """
    Produce weather alerts and FAO-56 Penman-Monteith crop evapotranspiration irrigation schedule.
    
    1. 100% Deterministic Physics & Agronomic Rule Calculation: Zero unverified ML.
    2. Context Personalization: If parameters are omitted and user is logged in,
       automatically loads the farmer's active farm profile (district, crop, sowing_date).
    3. Open Access: Accessible to unauthenticated visitors with sensible Rajasthan defaults.
    """
    target_district = district
    target_crop = crop
    target_sowing = sowing_date

    # Auto-fill from authenticated user's farm profile if parameters omitted
    if (not target_district or not target_crop or not target_sowing) and user and db is not None:
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
                target_sowing = target_sowing or farm.sowing_date
        except Exception as exc:
            logger.warning("Could not auto-fill weather parameters from farm profile: %s", exc)

    # Defaults if still unspecified
    target_district = target_district or "Kota"
    target_crop = target_crop or "Mustard"
    target_sowing = target_sowing or (date.today() - timedelta(days=35))

    return await get_irrigation_advisory(
        district=target_district,
        crop=target_crop,
        sowing_date=target_sowing,
        irrigation_type=irrigation_type,
    )
