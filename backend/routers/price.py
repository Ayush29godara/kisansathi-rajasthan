"""Mandi price trends and 2-4 week forecast endpoints."""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user_optional
from app.db import get_db
from app.models import FarmModel
from app.schemas import MandiPriceForecastResponse
from services.price_service import get_mandi_price_forecast

logger = logging.getLogger("kisansathi.price_router")

router = APIRouter(prefix="", tags=["Mandi Prices"])


@router.get("/forecast/price", response_model=MandiPriceForecastResponse)
async def forecast_price(
    mandi: Optional[str] = Query(None, description="Mandi name in Rajasthan (e.g. Alwar, Kota, Bikaner)"),
    commodity: Optional[str] = Query(None, description="Agricultural commodity name (e.g. Mustard, Wheat, Bajra)"),
    days: int = Query(30, ge=7, le=90, description="Historical days of daily APMC prices to retrieve"),
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
    db: Optional[Session] = Depends(get_db),
):
    """
    Produce mandi price trends, 2-4 week forecast ranges, and sell/wait guidance.
    
    1. Publicly accessible: Open to unauthenticated farmers and demo mode.
    2. Context personalization: If user is logged in and parameters are omitted,
       auto-fills from the farmer's registered farm profile.
    3. Model integrity: Uses LightGBM quantile regression when models are trained;
       otherwise transparently returns the persistence baseline with model_version='baseline'.
    """
    target_mandi = mandi
    target_commodity = commodity

    # Auto-fill from authenticated user's farm profile if parameters omitted
    if (not target_mandi or not target_commodity) and user and db is not None:
        try:
            farm = (
                db.query(FarmModel)
                .filter(FarmModel.user_id == str(user["id"]))
                .order_by(FarmModel.updated_at.desc())
                .first()
            )
            if farm:
                target_mandi = target_mandi or farm.district
                target_commodity = target_commodity or farm.crop
        except Exception as exc:
            logger.warning("Could not auto-fill mandi parameters from farm profile: %s", exc)

    # Sensible defaults for Rajasthan
    target_mandi = target_mandi or "Alwar"
    target_commodity = target_commodity or "Mustard"

    return get_mandi_price_forecast(
        mandi=target_mandi,
        commodity=target_commodity,
        days=days,
        db=db,
    )
