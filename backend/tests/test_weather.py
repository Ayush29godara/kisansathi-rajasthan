"""Unit and integration tests for Weather service and FAO-56 Penman-Monteith ET0 calculation."""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient

from services.weather_service import (
    calculate_fao56_penman_monteith,
    determine_crop_stage_and_kc,
    evaluate_weather_alerts,
    get_irrigation_advisory,
)


def test_fao56_penman_monteith_textbook_reference():
    """
    Test FAO-56 Penman-Monteith ET0 equation against known textbook benchmark (FAO-56 Paper, Example 18).
    
    Given meteorological observations:
        T_max = 21.5°C, T_min = 12.3°C (T_mean = 16.9°C)
        RH_mean = 73.5% (approx average of 84% and 63%)
        u2 = 2.078 m/s
        Rn = 14.4 MJ/m²/day
        elevation = 100 m
    
    The benchmark reference ET0 is ~4.1 mm/day.
    """
    et0 = calculate_fao56_penman_monteith(
        temp_max_c=21.5,
        temp_min_c=12.3,
        rh_mean_pct=73.5,
        wind_speed_2m_ms=2.078,
        solar_radiation_mj=14.4,
        elevation_m=100.0,
    )
    # Must match benchmark within numerical rounding tolerance (FAO-56 standard benchmark ~4.0-4.1 mm/day)
    assert 3.8 <= et0 <= 4.3
    assert et0 == pytest.approx(4.01, abs=0.2)


def test_fao56_penman_monteith_extreme_climates():
    """Verify ET0 scales physically for hot arid summer vs cool winter conditions."""
    # 1. Hot Arid Summer (Western Rajasthan May/June)
    et0_summer = calculate_fao56_penman_monteith(
        temp_max_c=43.0,
        temp_min_c=27.0,
        rh_mean_pct=22.0,
        wind_speed_2m_ms=3.8,
        solar_radiation_mj=24.0,
        elevation_m=230.0,
    )
    assert 8.0 <= et0_summer <= 15.0

    # 2. Cool Winter (North-Eastern Rajasthan January)
    et0_winter = calculate_fao56_penman_monteith(
        temp_max_c=21.0,
        temp_min_c=6.0,
        rh_mean_pct=55.0,
        wind_speed_2m_ms=1.2,
        solar_radiation_mj=13.0,
        elevation_m=270.0,
    )
    assert 2.0 <= et0_winter <= 4.0
    assert et0_summer > et0_winter


def test_crop_stage_and_kc_determination():
    """Verify phenological stage and Kc factor transitions from sowing date."""
    # Mustard (125-day total cycle)
    # Day 10: Initial Germination stage, Kc ~ 0.35
    stage_ini, kc_ini, root_ini, p_ini = determine_crop_stage_and_kc("Mustard", days_since_sowing=10)
    assert "Initial" in stage_ini or "अंकुरण" in stage_ini
    assert kc_ini == 0.35
    assert root_ini <= 0.40

    # Day 70: Mid-Season Flowering & Pod formation, Kc ~ 1.15
    stage_mid, kc_mid, root_mid, p_mid = determine_crop_stage_and_kc("Mustard", days_since_sowing=70)
    assert "Flowering" in stage_mid or "फूल" in stage_mid
    assert kc_mid == 1.15
    assert root_mid >= 0.90

    # Wheat (130-day total cycle)
    # Day 14: Crown Root Initiation (CRI) stage
    stage_cri, kc_cri, _, _ = determine_crop_stage_and_kc("Wheat", days_since_sowing=14)
    assert "CRI" in stage_cri or "Crown Root" in stage_cri
    assert kc_cri == 0.40

    # Day 75: Flowering & Milking stage
    stage_wheat_mid, kc_wheat_mid, _, _ = determine_crop_stage_and_kc("Wheat", days_since_sowing=75)
    assert "Flowering" in stage_wheat_mid or "फूल" in stage_wheat_mid
    assert kc_wheat_mid == 1.15


def test_weather_alerts_frost_rule():
    """Verify frost alert triggers with university source citation when temp_min <= 4°C."""
    weather = {
        "temp_min": 2.5,
        "temp_max": 20.0,
        "humidity": 60.0,
        "precipitation_72h": 0.0,
        "wind_speed_kmh": 6.0,
    }
    alerts = evaluate_weather_alerts("Mustard", "Flowering & Pod Formation", weather)
    frost_alerts = [a for a in alerts if "Frost" in a.alert_type or "पाला" in a.alert_type]
    assert len(frost_alerts) == 1
    assert frost_alerts[0].severity in ("warning", "critical")
    assert "Kota" in frost_alerts[0].source or "AU" in frost_alerts[0].source or "Jobner" in frost_alerts[0].source


def test_weather_alerts_disease_risk_rule():
    """Verify cloudy/humid disease alert triggers when humidity >= 80% with moderate temps."""
    weather = {
        "temp_min": 14.0,
        "temp_max": 22.0,
        "humidity": 86.0,
        "precipitation_72h": 2.0,
        "wind_speed_kmh": 10.0,
    }
    alerts = evaluate_weather_alerts("Mustard", "Flowering & Pod Formation", weather)
    disease_alerts = [a for a in alerts if "Disease Risk" in a.alert_type or "रोग जोखिम" in a.alert_type]
    assert len(disease_alerts) == 1
    assert disease_alerts[0].severity == "warning"
    assert "DRMR" in disease_alerts[0].source or "Bharatpur" in disease_alerts[0].source or "ICAR" in disease_alerts[0].source


def test_weather_alerts_rain_withholding_urgency():
    """Verify forecasted heavy rain triggers withhold_due_to_rain urgency."""
    weather = {
        "temp_min": 18.0,
        "temp_max": 30.0,
        "humidity": 75.0,
        "precipitation_72h": 22.0,  # >= 10 mm
        "wind_speed_kmh": 14.0,
    }
    alerts = evaluate_weather_alerts("Wheat", "Tillering", weather)
    rain_alerts = [a for a in alerts if "स्थगित" in a.alert_type or "Rain" in a.alert_type or "वर्षा" in a.alert_type]
    assert len(rain_alerts) == 1
    assert "IMD" in rain_alerts[0].source or "AAS" in rain_alerts[0].source


@pytest.mark.asyncio
async def test_get_irrigation_advisory_deterministic_physics():
    """Verify full irrigation advisory produces complete FAO-56 response without ML."""
    res = await get_irrigation_advisory(
        district="Kota",
        crop="Mustard",
        sowing_date=date.today() - timedelta(days=60),
        irrigation_type="tubewell",
    )
    assert res.district == "Kota"
    assert res.crop == "Mustard"
    assert res.et0_mm_day > 0
    assert res.kc_factor > 0
    assert res.crop_etc_mm_day == pytest.approx(res.kc_factor * res.et0_mm_day, abs=0.05)
    assert res.next_irrigation_due_days >= 1
    assert res.water_depth_mm > 0
    assert res.irrigation_urgency in ("normal", "due_soon", "immediate", "withhold_due_to_rain")
    assert "FAO-56" in res.methodology
    assert "zero ML" in res.methodology or "Zero ML" in res.methodology


def test_api_weather_advice_unauthenticated_succeeds(client: TestClient):
    """Ensure /advice/weather is accessible without auth (public agronomic decision support)."""
    response = client.get("/advice/weather?district=Alwar&crop=Wheat&sowing_date=2026-10-15")
    assert response.status_code == 200
    data = response.json()
    assert data["district"] == "Alwar"
    assert data["crop"] == "Wheat"
    assert "et0_mm_day" in data
    assert "kc_factor" in data
    assert "crop_etc_mm_day" in data
    assert "current_growth_stage" in data
    assert "next_irrigation_due_days" in data
    assert "irrigation_urgency" in data
    assert "advisory_text" in data
    assert "methodology" in data


def test_api_weather_advice_authenticated(client: TestClient, auth_headers: dict):
    """Ensure /advice/weather returns valid schedule when authenticated."""
    response = client.get(
        "/advice/weather?district=Kota&crop=Mustard",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["district"] == "Kota"
    assert data["crop"] == "Mustard"
    assert data["et0_mm_day"] > 0
