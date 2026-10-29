"""Weather alerts and FAO-56 irrigation advisory endpoints."""

from datetime import date
from typing import Dict, Any
from fastapi import APIRouter, Depends, Query
from app.auth import get_current_user
from app.schemas import IrrigationScheduleResponse
from services.weather_service import get_irrigation_advisory

router = APIRouter(prefix="", tags=["Weather & Irrigation"])


@router.get("/advice/weather", response_model=IrrigationScheduleResponse)
async def get_weather_and_irrigation_advice(
    district: str = Query(..., description="Rajasthan district name"),
    crop: str = Query(..., description="Crop name"),
    sowing_date: date = Query(..., description="Sowing date (YYYY-MM-DD)"),
    irrigation_type: str = Query("tubewell", description="canal/tubewell/well/rainfed"),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Produce weather alerts and FAO-56 Penman-Monteith irrigation schedule.
    
    100% deterministic physics & agronomic calculation; no unverified ML.
    """
    return get_irrigation_advisory(
        district=district,
        crop=crop,
        sowing_date=sowing_date,
        irrigation_type=irrigation_type,
    )
