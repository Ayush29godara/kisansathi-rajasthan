"""Unit and integration tests for Mandi Price forecasting and decision support."""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from services.price_service import (
    determine_recommendation,
    load_historical_prices,
    get_mandi_price_forecast,
    BENCHMARK_MODAL_PRICES,
)
import services.price_service as price_service_module


def test_determine_recommendation_rules():
    """Ensure price trend and 'sell now / wait' decision support rules trigger correctly."""
    # Bullish > +2.5% -> Wait
    trend_hi, rec_hi, hint_hi = determine_recommendation(3.8, language="hi")
    assert trend_hi == "bullish"
    assert rec_hi == "wait"
    assert "रुकें" in hint_hi

    trend_en, rec_en, hint_en = determine_recommendation(4.5, language="en")
    assert trend_en == "bullish"
    assert rec_en == "wait"
    assert "Wait:" in hint_en

    # Bearish < -2.5% -> Sell Now
    trend_hi, rec_hi, hint_hi = determine_recommendation(-3.2, language="hi")
    assert trend_hi == "bearish"
    assert rec_hi == "sell_now"
    assert "तुरंत बेचें" in hint_hi

    trend_en, rec_en, hint_en = determine_recommendation(-5.0, language="en")
    assert trend_en == "bearish"
    assert rec_en == "sell_now"
    assert "Sell Now:" in hint_en

    # Stable within ±2.5% -> Hold
    trend_hi, rec_hi, hint_hi = determine_recommendation(0.5, language="hi")
    assert trend_hi == "stable"
    assert rec_hi == "hold"
    assert "सामान्य" in hint_hi


def test_load_historical_prices_window():
    """Verify historical prices can be loaded and respect requested window length."""
    records_15 = load_historical_prices(mandi="Alwar", commodity="Mustard", days=15)
    assert len(records_15) == 15
    assert records_15[-1].modal_price > 0
    assert records_15[-1].min_price <= records_15[-1].max_price

    records_30 = load_historical_prices(mandi="Kota", commodity="Soybean", days=30)
    assert len(records_30) == 30
    assert records_30[0].price_date <= records_30[-1].price_date


def test_baseline_price_forecast_output():
    """Ensure baseline fallback returns honest version and valid expanding uncertainty ranges."""
    forecast = get_mandi_price_forecast(mandi="Alwar", commodity="Mustard")

    assert forecast.mandi == "Alwar"
    assert forecast.commodity == "Mustard"
    assert forecast.model_version == "baseline"
    assert forecast.latest_modal_price > 0
    assert forecast.trend in ("bullish", "bearish", "stable")
    assert forecast.recommendation in ("sell_now", "wait", "hold")
    assert len(forecast.recommendation_text) > 5

    # 2-Week interval: min <= expected <= max
    assert forecast.forecast_2_weeks.min_expected <= forecast.forecast_2_weeks.expected_modal
    assert forecast.forecast_2_weeks.expected_modal <= forecast.forecast_2_weeks.max_expected

    # 4-Week interval: min <= expected <= max
    assert forecast.forecast_4_weeks.min_expected <= forecast.forecast_4_weeks.expected_modal
    assert forecast.forecast_4_weeks.expected_modal <= forecast.forecast_4_weeks.max_expected

    # Uncertainty expands over time (4-week range is wider than 2-week range)
    width_2w = forecast.forecast_2_weeks.max_expected - forecast.forecast_2_weeks.min_expected
    width_4w = forecast.forecast_4_weeks.max_expected - forecast.forecast_4_weeks.min_expected
    assert width_4w >= width_2w

    # Must contain disclaimer
    assert "मार्गदर्शन" in forecast.disclaimer


def test_synthetic_model_inference_fixture():
    """Verify that when a trained model is provided, model predictions are applied and labeled."""
    class SyntheticQuantileModel:
        model_version = "synthetic-test-v2.0"

        def predict(self, price: float):
            # Simulate a bullish forecast (+5%)
            return {
                "2wk_q10": price * 1.02,
                "2wk_q50": price * 1.05,
                "2wk_q90": price * 1.09,
                "4wk_q10": price * 1.01,
                "4wk_q50": price * 1.06,
                "4wk_q90": price * 1.12,
            }

    synthetic_model = SyntheticQuantileModel()
    price_service_module.TEST_ONLY_SYNTHETIC_PRICE_MODEL = synthetic_model

    try:
        forecast = get_mandi_price_forecast(mandi="Bikaner", commodity="Guar")
        assert forecast.model_version == "synthetic-test-v2.0"
        assert forecast.trend == "bullish"
        assert forecast.recommendation == "wait"
        assert forecast.forecast_2_weeks.expected_modal > forecast.latest_modal_price
    finally:
        price_service_module.TEST_ONLY_SYNTHETIC_PRICE_MODEL = None


def test_api_forecast_price_unauthenticated(client: TestClient):
    """Ensure /forecast/price is accessible without auth (public market transparency)."""
    response = client.get("/forecast/price")
    assert response.status_code == 200
    data = response.json()
    assert data["mandi"] == "Alwar"
    assert data["commodity"] == "Mustard"
    assert "latest_modal_price" in data
    assert "forecast_2_weeks" in data
    assert "forecast_4_weeks" in data
    assert "trend" in data
    assert "recommendation" in data
    assert "disclaimer" in data


def test_api_forecast_price_custom_query(client: TestClient, auth_headers: dict):
    """Ensure /forecast/price respects mandi, commodity, and days query parameters."""
    response = client.get(
        "/forecast/price?mandi=Kota&commodity=Soybean&days=15",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mandi"] == "Kota"
    assert data["commodity"] == "Soybean"
    assert len(data["history"]) <= 15
    assert data["forecast_2_weeks"]["expected_modal"] > 0
