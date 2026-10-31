"""Unit and integration tests for District Yield Prediction and Baseline Fallback Pipeline.

Includes a clearly marked synthetic fixture used strictly for unit testing.
"""

import os
import json
import pickle
from datetime import date
import pytest
from fastapi.testclient import TestClient
from services.yield_service import (
    get_district_yield_outlook,
    map_to_statistical_district,
    HISTORICAL_5YR_MEANS_KG_HA,
)
from app.db import SessionLocal
from app.models import FarmModel

# ===========================================================================
# CLEARLY MARKED SYNTHETIC TEST FIXTURE (USED ONLY FOR UNIT TESTING)
# ===========================================================================
TEST_ONLY_SYNTHETIC_YIELD_DATA = {
    "district": "Kotputli-Behror",
    "parent_district": "Alwar",
    "crop": "Mustard",
    "season": "Rabi",
    "forecast_year": 2026,
    "synthetic_feature_vector": [580.0, 14, 26, 20, 8.5, 1820.0, 0.82],
    "expected_baseline_mean_kg_ha": 1820.0,
}


class TinySyntheticRegressor:
    """Tiny mock model fixture used strictly for testing model loading without heavy dependencies."""
    def __init__(self, multiplier: float = 1.05):
        self.multiplier = multiplier

    def predict(self, X):
        # Predict yield as baseline lag_yield * multiplier
        return [float(X[0][5]) * self.multiplier]


def test_district_boundary_mapping():
    """Verify that 2023 reorganized districts map to the 33-district statistical baseline."""
    assert map_to_statistical_district("Kotputli-Behror") == "Alwar"
    assert map_to_statistical_district("kotputli behror") == "Alwar"
    assert map_to_statistical_district("Balotra") == "Barmer"
    assert map_to_statistical_district("Anupgarh") == "Sri Ganganagar"
    assert map_to_statistical_district("Phalodi") == "Jodhpur"
    assert map_to_statistical_district("Didwana-Kuchaman") == "Nagaur"
    assert map_to_statistical_district("Jaipur Rural") == "Jaipur"
    assert map_to_statistical_district("Jaipur") == "Jaipur"


def test_baseline_fallback_honesty():
    """Verify that when no trained ML model exists, the response honestly reports 'baseline'."""
    # Gram has no district time series, so it must fall back to the reference table
    outlook = get_district_yield_outlook(
        district="Jaipur",
        crop="Gram",
        season="Rabi",
        forecast_year=2026,
    )

    # Per project honesty guidelines:
    assert outlook.model_version == "baseline"
    assert outlook.predicted_yield_kg_ha == HISTORICAL_5YR_MEANS_KG_HA["gram"]["Jaipur"]
    assert outlook.baseline_5yr_mean_kg_ha == HISTORICAL_5YR_MEANS_KG_HA["gram"]["Jaipur"]
    assert len(outlook.top_drivers) >= 2
    assert "baseline" in outlook.summary_text.lower() or "बेसलाइन" in outlook.summary_text


def test_predict_yield_unauthenticated_fails(client: TestClient):
    """GET /predict/yield without authentication must return 401 Unauthorized."""
    response = client.get("/predict/yield?district=Jaipur&crop=Mustard")
    assert response.status_code == 401


def test_predict_yield_authenticated_succeeds(client: TestClient, auth_headers: dict):
    """GET /predict/yield with valid token returns schema-compliant YieldOutlookResponse."""
    response = client.get(
        "/predict/yield?district=Alwar&crop=Mustard&season=Rabi&year=2026",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["district"] == "Alwar"
    assert data["crop"] == "Mustard"
    assert data["season"] == "Rabi"
    assert data["forecast_year"] == 2026
    assert data["predicted_yield_kg_ha"] > 0
    assert data["baseline_5yr_mean_kg_ha"] > 0
    assert data["model_version"] in ("baseline", "ml-xgb-v1.0", "district-trend-v1")
    assert isinstance(data["top_drivers"], list)
    assert len(data["top_drivers"]) >= 2
    assert data["top_drivers"][0]["feature"]
    assert data["top_drivers"][0]["impact"] in ("positive", "negative", "neutral")


def test_predict_yield_auto_fills_from_user_farm_profile(client: TestClient, auth_headers: dict):
    """Verify that omitting query parameters causes endpoint to auto-populate from farmer's registered farm."""
    # Seed farm profile in database
    if SessionLocal:
        db = SessionLocal()
        try:
            # Create farm for test user 'farmer_12345'
            farm = FarmModel(
                user_id="farmer_12345",
                district="Kota",
                tehsil="Digod",
                crop="Soybean",
                land_hectare=3.0,
                irrigation="canal",
                sowing_date=date(2026, 7, 1),
            )
            db.add(farm)
            db.commit()
        finally:
            db.close()

    # Call endpoint without district/crop query parameters
    response = client.get("/predict/yield", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    # Must resolve to the farmer's registered district (Kota) and crop (Soybean)
    assert data["district"] == "Kota"
    assert data["crop"] == "Soybean"
    assert data["predicted_yield_kg_ha"] > 0
    assert data["model_version"] == "district-trend-v1"


def test_synthetic_model_loading_and_inference(monkeypatch):
    """Verify that when a valid model artifact is present, the service runs ML inference and updates model_version."""
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml", "models"))
    os.makedirs(models_dir, exist_ok=True)

    test_model_path = os.path.join(models_dir, "yield_gram_xgb.joblib")
    test_meta_path = os.path.join(models_dir, "yield_gram_metadata.json")

    # Create tiny synthetic model file using pickle
    dummy_model = TinySyntheticRegressor(multiplier=1.12)
    with open(test_model_path, "wb") as f:
        pickle.dump(dummy_model, f)

    with open(test_meta_path, "w", encoding="utf-8") as f:
        json.dump({
            "model_version": "test-xgb-gram-v1.0",
            "features": ["monsoon_total_mm", "longest_dry_spell_days", "rainy_days", "heat_stress_days", "winter_min_temp_c", "lag_1_yield", "irrigated_share"]
        }, f)

    try:
        outlook = get_district_yield_outlook(
            district="Bikaner",
            crop="Gram",
            season="Rabi",
            forecast_year=2026,
        )

        assert outlook.model_version == "test-xgb-gram-v1.0"
        # Bikaner baseline for gram is 920 kg/ha * 1.12 multiplier = ~1030.4 kg/ha
        assert outlook.predicted_yield_kg_ha > outlook.baseline_5yr_mean_kg_ha
        assert outlook.predicted_yield_kg_ha == pytest.approx(920.0 * 1.12, rel=1e-2)

    finally:
        # Clean up test artifact files
        if os.path.exists(test_model_path):
            os.remove(test_model_path)
        if os.path.exists(test_meta_path):
            os.remove(test_meta_path)


def test_yield_varies_by_district_and_crop():
    """Estimates must differ across districts and crops (no single shared default)."""
    districts = ["Jaipur", "Kota", "Bikaner", "Udaipur", "Sri Ganganagar", "Barmer"]
    for crop in ("Mustard", "Wheat", "Bajra"):
        values = {
            d: get_district_yield_outlook(d, crop, "Rabi", 2026).predicted_yield_kg_ha
            for d in districts
        }
        assert len(set(values.values())) == len(districts), (crop, values)
    wheat = get_district_yield_outlook("Kota", "Wheat", "Rabi", 2026).predicted_yield_kg_ha
    bajra = get_district_yield_outlook("Kota", "Bajra", "Kharif", 2026).predicted_yield_kg_ha
    assert wheat != bajra


def test_yield_unsupported_crop_returns_404(client: TestClient, auth_headers: dict):
    """Unknown crops must not silently receive a generic number."""
    response = client.get("/predict/yield?district=Jaipur&crop=Tomato", headers=auth_headers)
    assert response.status_code == 404
