"""Mandi price trends and 2-4 week forecast endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, Query
from app.auth import get_current_user
from app.schemas import MandiPriceForecastResponse
from services.price_service import get_mandi_price_forecast

router = APIRouter(prefix="", tags=["Mandi Prices"])


@router.get("/forecast/price", response_model=MandiPriceForecastResponse)
async def forecast_price(
    mandi: str = Query(..., description="Mandi name in Rajasthan (e.g. Alwar, Kota, Bikaner)"),
    commodity: str = Query(..., description="Agricultural commodity name (e.g. Mustard, Wheat, Bajra)"),
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Produce mandi price trends and 2-4 week forecast ranges.
    
    Reports baseline persistence forecast until trained time-series models exist,
    explicitly marking model_version = 'baseline'.
    """
    return get_mandi_price_forecast(mandi=mandi, commodity=commodity)
