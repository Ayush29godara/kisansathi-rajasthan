"""District yield prediction and driver attribution endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, Query
from app.auth import get_current_user
from app.schemas import YieldOutlookResponse
from services.yield_service import get_district_yield_outlook

router = APIRouter(prefix="", tags=["Yield Outlook"])


@router.get("/predict/yield", response_model=YieldOutlookResponse)
async def predict_yield(
    district: str = Query(..., description="District name in Rajasthan"),
    crop: str = Query(..., description="Crop name"),
    season: str = Query("Kharif", description="Kharif or Rabi"),
    year: int = Query(2026, description="Crop forecast year"),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Produce district crop yield outlook and key drivers.
    
    Reports baseline statistics (5-year historical district mean) until real trained
    models are present, explicitly marking model_version = 'baseline'.
    """
    return get_district_yield_outlook(
        district=district,
        crop=crop,
        season=season,
        forecast_year=year,
    )
