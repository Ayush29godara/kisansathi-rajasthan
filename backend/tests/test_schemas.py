"""Unit tests for Pydantic schema validation and integrity."""

import pytest
from datetime import date
from pydantic import ValidationError
from app.schemas import (
    FarmCreate,
    ChatRequest,
    DiseaseRecordCreate,
    YieldOutlookResponse,
    MandiPriceForecastResponse,
    IrrigationScheduleResponse,
)


def test_farm_create_validation():
    """Ensure farm creation validates land size and required fields."""
    # Valid schema
    farm = FarmCreate(
        district="Kota",
        tehsil="Digod",
        crop="Soybean",
        land_hectare=3.2,
        irrigation="canal",
        sowing_date=date(2026, 7, 5),
    )
    assert farm.land_hectare == 3.2

    # Negative land area must fail validation
    with pytest.raises(ValidationError):
        FarmCreate(
            district="Kota",
            tehsil="Digod",
            crop="Soybean",
            land_hectare=-1.0,
            irrigation="canal",
            sowing_date=date(2026, 7, 5),
        )


def test_chat_request_validation():
    """Ensure empty question fails validation."""
    with pytest.raises(ValidationError):
        ChatRequest(question="")


def test_baseline_reporting_in_yield():
    """Ensure yield schema accepts baseline attribution."""
    outlook = YieldOutlookResponse(
        district="Alwar",
        crop="Mustard",
        season="Rabi",
        forecast_year=2026,
        predicted_yield_kg_ha=1780.0,
        baseline_5yr_mean_kg_ha=1780.0,
        model_version="baseline",
        summary_text="Baseline mean calculation",
    )
    assert outlook.model_version == "baseline"
