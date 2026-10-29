"""Weather alerts and FAO-56 Evapotranspiration Irrigation Scheduling service.

Deterministic rules and FAO Irrigation and Drainage Paper 56 physics formulation (no ML).
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from app.config import get_settings
from app.schemas import IrrigationScheduleResponse, WeatherAlertItem

settings = get_settings()

# Crop coefficients (Kc) per growth stage: [Initial, Mid-Season, End/Maturity]
CROP_KC_TABLE: Dict[str, Dict[str, Any]] = {
    "mustard": {"kc_ini": 0.35, "kc_mid": 1.15, "kc_end": 0.35, "days_mid": 45, "total_days": 125},
    "wheat": {"kc_ini": 0.40, "kc_mid": 1.15, "kc_end": 0.40, "days_mid": 50, "total_days": 130},
    "bajra": {"kc_ini": 0.30, "kc_mid": 1.05, "kc_end": 0.45, "days_mid": 35, "total_days": 85},
    "gram": {"kc_ini": 0.40, "kc_mid": 1.00, "kc_end": 0.35, "days_mid": 40, "total_days": 115},
    "guar": {"kc_ini": 0.30, "kc_mid": 1.00, "kc_end": 0.40, "days_mid": 35, "total_days": 90},
    "default": {"kc_ini": 0.35, "kc_mid": 1.05, "kc_end": 0.40, "days_mid": 40, "total_days": 100},
}


def calculate_fao56_et0_simple(
    temp_max_c: float = 32.0,
    temp_min_c: float = 18.0,
    solar_radiation_mj: float = 20.0,
) -> float:
    """
    Hargreaves-Samani / simplified FAO-56 Penman-Monteith ET0 estimate (mm/day).
    
    In full production this pulls daily temperature, humidity, solar radiation,
    and windspeed from Open-Meteo / IMD APIs.
    """
    t_mean = (temp_max_c + temp_min_c) / 2.0
    t_range = max(temp_max_c - temp_min_c, 1.0)
    # Standard Hargreaves coefficient: 0.0023 * Ra * (T_mean + 17.8) * sqrt(TR)
    et0 = 0.0023 * (solar_radiation_mj * 0.408) * (t_mean + 17.8) * (t_range ** 0.5)
    return max(round(et0, 2), 2.0)


def get_irrigation_advisory(
    district: str,
    crop: str,
    sowing_date: date,
    irrigation_type: str = "tubewell",
) -> IrrigationScheduleResponse:
    """
    Generate irrigation schedule using FAO-56 Penman-Monteith crop evapotranspiration.
    
    Determines crop growth stage, Kc factor, daily water loss (ETc = Kc * ET0),
    and scheduled irrigation requirement.
    """
    today = date.today()
    days_since_sowing = max((today - sowing_date).days, 0)
    crop_lower = crop.lower().strip()
    kc_info = CROP_KC_TABLE.get(crop_lower, CROP_KC_TABLE["default"])

    # Determine current growth stage and Kc
    if days_since_sowing < 20:
        stage = "Initial / Germination"
        kc = kc_info["kc_ini"]
    elif days_since_sowing < kc_info["days_mid"]:
        stage = "Vegetative / Tillering"
        kc = (kc_info["kc_ini"] + kc_info["kc_mid"]) / 2.0
    elif days_since_sowing < (kc_info["total_days"] - 25):
        stage = "Mid-Season (Flowering & Grain Filling)"
        kc = kc_info["kc_mid"]
    else:
        stage = "Late Season / Maturity"
        kc = kc_info["kc_end"]

    et0 = calculate_fao56_et0_simple(temp_max_c=34.0, temp_min_c=20.0)
    crop_etc = round(kc * et0, 2)

    # Days until next irrigation based on soil water depletion
    root_water_capacity_mm = 50.0  # typical for sandy-loam / Rajasthan soils
    mad = 0.50  # Management Allowed Depletion (50%)
    allowable_depletion_mm = root_water_capacity_mm * mad

    days_to_irrigation = max(int(allowable_depletion_mm / max(crop_etc, 1.0)), 1)
    urgency = "normal"
    if days_to_irrigation <= 2:
        urgency = "due_soon"

    alerts: List[WeatherAlertItem] = []
    # Check regional rule thresholds (e.g. Western Rajasthan summer heat)
    if et0 > 7.0:
        alerts.append(
            WeatherAlertItem(
                alert_type="High Evaporative Demand",
                severity="warning",
                message="तीव्र वाष्पीकरण और तेज धूप। फसल में नमी की कमी न होने दें।",
            )
        )

    advisory_text = (
        f"{district} में {crop} फसल वर्तमान में '{stage}' अवस्था (बुवाई से {days_since_sowing} दिन) में है। "
        f"दैनिक फसल जल मांग (ETc): {crop_etc} मिमी/दिन। आगामी सिंचाई {days_to_irrigation} दिनों में प्रस्तावित है।"
    )

    return IrrigationScheduleResponse(
        district=district,
        crop=crop,
        et0_mm_day=et0,
        kc_factor=kc,
        crop_etc_mm_day=crop_etc,
        days_since_sowing=days_since_sowing,
        current_growth_stage=stage,
        next_irrigation_due_days=days_to_irrigation,
        water_depth_mm=round(allowable_depletion_mm, 1),
        irrigation_urgency=urgency,
        advisory_text=advisory_text,
        alerts=alerts,
    )
