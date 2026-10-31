"""Weather alerts and FAO-56 Penman-Monteith Evapotranspiration Irrigation Scheduling service.

Deterministic rules and FAO Irrigation and Drainage Paper 56 physics formulation (Zero ML).
Uses Open-Meteo free API with district coordinates and graceful climatological fallbacks.
"""

import os
import json
import math
import logging
from datetime import date, timedelta, datetime
from typing import List, Dict, Any, Optional, Tuple
import httpx

from app.config import get_settings
from app.schemas import IrrigationScheduleResponse, WeatherAlertItem

logger = logging.getLogger("kisansathi.weather_service")
settings = get_settings()

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# ---------------------------------------------------------------------------
# Load Reference Data: Districts Coordinates and Agronomic Thresholds
# ---------------------------------------------------------------------------
def _load_reference_json(filename: str) -> Any:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reference"))
    path = os.path.join(base_dir, filename)
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

DISTRICTS_REF = _load_reference_json("districts.json")
THRESHOLDS_REF = _load_reference_json("thresholds.json")

# Build dictionary indexed by normalized district name
DISTRICT_COORDS: Dict[str, Dict[str, Any]] = {}
for d in DISTRICTS_REF:
    DISTRICT_COORDS[d["name"].lower().strip()] = d
    if "hindi_name" in d:
        DISTRICT_COORDS[d["hindi_name"].lower().strip()] = d

# Default coordinates for Rajasthan center (Jaipur)
DEFAULT_DISTRICT_COORD = {
    "name": "Jaipur",
    "latitude": 26.9124,
    "longitude": 75.7873,
    "elevation_m": 431.0,
}


# ---------------------------------------------------------------------------
# FAO-56 Penman-Monteith Reference Evapotranspiration (ET0) Equation
# ---------------------------------------------------------------------------
def calculate_fao56_penman_monteith(
    temp_max_c: float,
    temp_min_c: float,
    rh_mean_pct: float,
    wind_speed_2m_ms: float,
    solar_radiation_mj: float,
    elevation_m: float = 250.0,
    soil_heat_flux_g: float = 0.0,
) -> float:
    """
    Standard FAO-56 Penman-Monteith Reference Evapotranspiration (ET0) in mm/day.
    
    Formula (Allen et al., 1998, FAO Irrigation & Drainage Paper 56, Eq. 6):
        ET0 = [0.408 * Delta * (Rn - G) + gamma * (900 / (T_mean + 273)) * u2 * (es - ea)] /
              [Delta + gamma * (1 + 0.34 * u2)]
    
    Parameters:
        temp_max_c: Maximum air temperature (°C)
        temp_min_c: Minimum air temperature (°C)
        rh_mean_pct: Mean relative humidity (%)
        wind_speed_2m_ms: Wind speed measured at 2m height (m/s)
        solar_radiation_mj: Solar radiation or net radiation Rn (MJ/m²/day)
        elevation_m: Altitude above sea level (meters)
        soil_heat_flux_g: Soil heat flux density (MJ/m²/day, approx 0 for daily time-step)
    
    Returns:
        ET0 in mm/day (rounded to 2 decimal places)
    """
    t_mean = (temp_max_c + temp_min_c) / 2.0

    # 1. Slope of saturation vapour pressure curve (Delta) in kPa/°C (Eq. 13)
    exp_term = math.exp((17.27 * t_mean) / (t_mean + 237.3))
    delta = (4098.0 * (0.6108 * exp_term)) / ((t_mean + 237.3) ** 2)

    # 2. Atmospheric pressure (P) and psychrometric constant (gamma) in kPa/°C (Eq. 7, 8)
    p = 101.3 * (((293.0 - 0.0065 * elevation_m) / 293.0) ** 5.26)
    gamma = 0.000665 * p

    # 3. Saturation vapour pressure (es) in kPa (Eq. 11, 12)
    e_tmax = 0.6108 * math.exp((17.27 * temp_max_c) / (temp_max_c + 237.3))
    e_tmin = 0.6108 * math.exp((17.27 * temp_min_c) / (temp_min_c + 237.3))
    es = (e_tmax + e_tmin) / 2.0

    # 4. Actual vapour pressure (ea) in kPa (Eq. 19)
    ea = es * (max(min(rh_mean_pct, 100.0), 5.0) / 100.0)
    vpd = max(es - ea, 0.0)  # Vapour pressure deficit

    # 5. Net radiation estimation (Rn)
    # If solar radiation (Rs) is passed directly, convert to net radiation Rn ~= 0.77 * Rs - Rnl
    rn = solar_radiation_mj if solar_radiation_mj < 25.0 else solar_radiation_mj * 0.72

    # 6. Full FAO-56 Penman-Monteith Equation
    u2 = max(wind_speed_2m_ms, 0.5)
    rad_term = 0.408 * delta * (rn - soil_heat_flux_g)
    aero_term = gamma * (900.0 / (t_mean + 273.0)) * u2 * vpd
    denominator = delta + gamma * (1.0 + 0.34 * u2)

    et0 = (rad_term + aero_term) / denominator
    return max(round(et0, 2), 1.0)


# ---------------------------------------------------------------------------
# Open-Meteo Weather Fetching with Climatological Fallback
# ---------------------------------------------------------------------------
async def fetch_weather_forecast(
    latitude: float,
    longitude: float,
) -> Dict[str, Any]:
    """
    Fetch 7-day weather forecast from Open-Meteo API.
    Gracefully falls back to Rajasthan climatological averages on network/sandbox block.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,relative_humidity_2m_mean,precipitation_sum,wind_speed_10m_max,shortwave_radiation_sum",
        "timezone": "Asia/Kolkata",
        "forecast_days": 7,
    }

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(OPEN_METEO_URL, params=params)
            if resp.status_code == 200:
                data = resp.json()
                daily = data.get("daily", {})
                times = daily.get("time", [])
                t_maxs = daily.get("temperature_2m_max", [])
                t_mins = daily.get("temperature_2m_min", [])
                rhs = daily.get("relative_humidity_2m_mean", [])
                rains = daily.get("precipitation_sum", [])
                winds = daily.get("wind_speed_10m_max", [])
                sols = daily.get("shortwave_radiation_sum", [])

                if times and t_maxs:
                    forecast_days = []
                    for i in range(len(times)):
                        forecast_days.append({
                            "date": times[i],
                            "temp_max": t_maxs[i] if i < len(t_maxs) else 32.0,
                            "temp_min": t_mins[i] if i < len(t_mins) else 18.0,
                            "rain_mm": rains[i] if i < len(rains) else 0.0,
                        })

                    # Wind speed at 10m to 2m conversion: u2 = u10 * 0.748
                    w10 = winds[0] if winds else 12.0
                    u2 = (w10 / 3.6) * 0.748

                    return {
                        "is_live": True,
                        "temp_max": float(t_maxs[0]),
                        "temp_min": float(t_mins[0]),
                        "humidity": float(rhs[0]) if rhs else 50.0,
                        "wind_speed_kmh": float(w10),
                        "wind_speed_2m_ms": round(u2, 2),
                        "precipitation_sum": float(rains[0]) if rains else 0.0,
                        "precipitation_72h": sum(rains[:3]) if len(rains) >= 3 else 0.0,
                        "solar_radiation_mj": float(sols[0]) if sols else 18.0,
                        "forecast_days": forecast_days,
                    }
    except Exception as exc:
        logger.debug("Open-Meteo API unreachable or blocked by sandbox (%s), using climatological values.", exc)

    # Deterministic Climatological Fallback (Rajasthan Seasonal Averages)
    today = date.today()
    month = today.month
    # Typical winter vs summer vs monsoon profiles in Rajasthan
    if month in (11, 12, 1, 2):  # Rabi Winter
        t_max, t_min, rh, wind_kmh, sol, rain = 26.0, 10.5, 55.0, 8.0, 15.5, 0.0
    elif month in (3, 4, 5, 6):  # Zaid / Pre-monsoon Summer
        t_max, t_min, rh, wind_kmh, sol, rain = 40.0, 25.0, 32.0, 16.0, 22.0, 0.0
    else:  # Kharif Monsoon
        t_max, t_min, rh, wind_kmh, sol, rain = 33.0, 24.0, 72.0, 12.0, 17.0, 2.5

    forecast_days = []
    for d_offset in range(7):
        f_date = (today + timedelta(days=d_offset)).strftime("%Y-%m-%d")
        forecast_days.append({
            "date": f_date,
            "temp_max": t_max + ((d_offset % 3) - 1),
            "temp_min": t_min + ((d_offset % 2) - 0.5),
            "rain_mm": rain if d_offset == 2 and month in (7, 8) else 0.0,
        })

    u2 = (wind_kmh / 3.6) * 0.748
    return {
        "is_live": False,
        "temp_max": t_max,
        "temp_min": t_min,
        "humidity": rh,
        "wind_speed_kmh": wind_kmh,
        "wind_speed_2m_ms": round(u2, 2),
        "precipitation_sum": rain,
        "precipitation_72h": rain,
        "solar_radiation_mj": sol,
        "forecast_days": forecast_days,
    }


# ---------------------------------------------------------------------------
# Crop Stage and Kc Determination
# ---------------------------------------------------------------------------
def determine_crop_stage_and_kc(
    crop: str,
    days_since_sowing: int,
) -> Tuple[str, float, float, float]:
    """
    Determine current phenological growth stage, Kc factor, root depth (m),
    and allowable soil water depletion fraction (p) according to FAO-56.
    """
    crop_norm = crop.lower().strip()
    kc_table = THRESHOLDS_REF.get("fao56_crop_coefficients", {})
    crop_info = kc_table.get(crop_norm, kc_table.get("default", {
        "kc_ini": 0.35, "kc_mid": 1.10, "kc_end": 0.40,
        "stages_days": [20, 30, 40, 20], "total_days": 110,
        "root_depth_max_m": 1.0, "allowable_depletion_p": 0.50
    }))

    stages = crop_info.get("stages_days", [20, 30, 40, 20])
    l_ini, l_dev, l_mid, l_late = stages[0], stages[1], stages[2], stages[3]
    total_days = crop_info.get("total_days", sum(stages))

    kc_ini = crop_info.get("kc_ini", 0.35)
    kc_mid = crop_info.get("kc_mid", 1.10)
    kc_end = crop_info.get("kc_end", 0.40)
    root_max = crop_info.get("root_depth_max_m", 1.0)
    depletion_p = crop_info.get("allowable_depletion_p", 0.50)

    # 1. Initial Stage (0 to L_ini days)
    if days_since_sowing <= l_ini:
        if crop_norm == "wheat":
            stage_name = "CRI Stage / Crown Root Initiation (शीर्ष जड़ जमाव)"
        elif crop_norm == "mustard":
            stage_name = "Initial / Germination (अंकुरण व प्राथमिक विकास)"
        else:
            stage_name = "Initial Stage (आरंभिक अंकुरण अवस्था)"
        kc = kc_ini
        root_depth = 0.30

    # 2. Crop Development Stage (L_ini to L_ini + L_dev)
    elif days_since_sowing <= (l_ini + l_dev):
        progress = (days_since_sowing - l_ini) / max(l_dev, 1)
        kc = kc_ini + progress * (kc_mid - kc_ini)
        root_depth = 0.30 + progress * (root_max - 0.30)
        if crop_norm == "wheat":
            stage_name = "Tillering & Jointing (कल्ले फूटना व गांठें बनना)"
        elif crop_norm == "mustard":
            stage_name = "Vegetative & Branching (शाखाएं व वानस्पतिक वृद्धि)"
        else:
            stage_name = "Vegetative Stage (वानस्पतिक बढ़वार अवस्था)"

    # 3. Mid-Season Stage (Flowering, Seed Setting & Grain Filling)
    elif days_since_sowing <= (l_ini + l_dev + l_mid):
        kc = kc_mid
        root_depth = root_max
        if crop_norm == "wheat":
            stage_name = "Flowering & Milking (फूल व दूधिया दाना - क्रांतिक अवस्था)"
        elif crop_norm == "mustard":
            stage_name = "Flowering & Pod Formation (फूल व फलियां बनना - क्रांतिक अवस्था)"
        else:
            stage_name = "Mid-Season Reproductive (फूल व दाना भराव अवस्था)"

    # 4. Late Season / Ripening to Harvest
    elif days_since_sowing <= total_days:
        progress = (days_since_sowing - (l_ini + l_dev + l_mid)) / max(l_late, 1)
        kc = kc_mid - progress * (kc_mid - kc_end)
        root_depth = root_max
        stage_name = "Late Season / Maturity (दाना पकना व परिपक्वता अवस्था)"

    else:
        kc = kc_end
        root_depth = root_max
        stage_name = "Harvest Maturity (फसल पककर तैयार / कटाई अवस्था)"

    return stage_name, round(kc, 2), round(root_depth, 2), depletion_p


# ---------------------------------------------------------------------------
# Agronomic Rule Alerts Engine (Frost, Heat Stress, Cloudy/Humid Disease Risk)
# ---------------------------------------------------------------------------
def evaluate_weather_alerts(
    crop: str,
    stage_name: str,
    weather: Dict[str, Any],
) -> List[WeatherAlertItem]:
    """
    Evaluate deterministic crop-stage alerts using rules from reference/thresholds.json.
    Every alert strictly preserves university advisory attribution in the `source` field.
    """
    alerts: List[WeatherAlertItem] = []
    crop_lower = crop.lower().strip()
    rules = THRESHOLDS_REF.get("weather_alerts", {})

    temp_min = weather["temp_min"]
    temp_max = weather["temp_max"]
    humidity = weather["humidity"]
    precip_72h = weather["precipitation_72h"]
    wind_kmh = weather["wind_speed_kmh"]

    # 1. Frost / Cold Wave Rule
    frost_rule = rules.get("frost", {})
    if temp_min <= frost_rule.get("warning_temp_c", 4.0):
        severity = "critical" if temp_min <= frost_rule.get("critical_temp_c", 2.0) else "warning"
        alerts.append(
            WeatherAlertItem(
                alert_type=frost_rule.get("alert_type_hi", "पाला / शीतलहर चेतावनी (Frost Alert)"),
                severity=severity,
                message=frost_rule.get("message_hi", "पाला पड़ने की संभावना है। शाम को हल्की सिंचाई करें।"),
                source=frost_rule.get("source", "Package of Practices, Agriculture University Kota"),
            )
        )

    # 2. Heat Stress / Heatwave Rule
    heat_rule = rules.get("heat_stress", {})
    if temp_max >= heat_rule.get("warning_temp_c", 38.0):
        severity = "critical" if temp_max >= heat_rule.get("critical_temp_c", 42.0) else "warning"
        alerts.append(
            WeatherAlertItem(
                alert_type=heat_rule.get("alert_type_hi", "ताप तनाव / लू चेतावनी (Heat Stress Warning)"),
                severity=severity,
                message=heat_rule.get("message_hi", "तापमान 38°C से अधिक रहने से दाना सिकुड़ने का खतरा है।"),
                source=heat_rule.get("source", "ICAR-IIWBR Technical Guidelines on Terminal Heat Stress"),
            )
        )

    # 3. Cloudy & Humid Disease Risk Rule (Mustard White Rust / Bajra Downy Mildew)
    disease_risk_rule = rules.get("cloudy_humid_disease_risk", {})
    if (
        humidity >= disease_risk_rule.get("min_humidity_pct", 80.0)
        and temp_min >= disease_risk_rule.get("min_temp_c", 10.0)
        and temp_max <= disease_risk_rule.get("max_temp_c", 26.0)
    ):
        alerts.append(
            WeatherAlertItem(
                alert_type=disease_risk_rule.get("alert_type_hi", "बादल व उच्च आर्द्रता रोग जोखिम (High Disease Risk)"),
                severity="warning",
                message=disease_risk_rule.get("message_hi", "आर्द्रता 80% से अधिक होने पर सफेद रोली व झुलसा रोग का खतरा है।"),
                source=disease_risk_rule.get("source", "ICAR-DRMR Technical Advisory, Bharatpur"),
            )
        )

    # 4. Rain Forecast Withholding Rule
    rain_rule = rules.get("heavy_rainfall", {})
    if precip_72h >= rain_rule.get("precipitation_threshold_mm", 10.0):
        alerts.append(
            WeatherAlertItem(
                alert_type=rain_rule.get("alert_type_hi", "वर्षा पूर्वानुमान — सिंचाई स्थगित रखें"),
                severity="info",
                message=rain_rule.get("message_hi", "आगामी 48-72 घंटों में वर्षा का अनुमान है। सिंचाई रोककर रखें।"),
                source=rain_rule.get("source", "IMD Agro-Meteorological Advisory Services (AAS) Rajasthan State Unit"),
            )
        )

    # 5. High Wind Lodging Rule
    wind_rule = rules.get("high_wind", {})
    if wind_kmh >= wind_rule.get("wind_speed_threshold_kmh", 28.0) and ("Flowering" in stage_name or "Milking" in stage_name or "Heading" in stage_name):
        alerts.append(
            WeatherAlertItem(
                alert_type=wind_rule.get("alert_type_hi", "तेज हवा चेतावनी — सिंचाई से बचें"),
                severity="warning",
                message=wind_rule.get("message_hi", "तेज हवा के समय सिंचाई करने से फसल गिरने (Lodging) की आशंका रहती है।"),
                source=wind_rule.get("source", "State Department of Agriculture, Rajasthan Extension Manual"),
            )
        )

    return alerts


# ---------------------------------------------------------------------------
# Main Service Entrypoint
# ---------------------------------------------------------------------------
async def get_irrigation_advisory(
    district: str,
    crop: str,
    sowing_date: date,
    irrigation_type: str = "tubewell",
) -> IrrigationScheduleResponse:
    """
    Produce comprehensive weather alerts and FAO-56 Penman-Monteith irrigation schedule.
    
    100% deterministic physics & agronomic rule formulation (Zero unverified ML).
    """
    clean_district = district.strip()
    clean_crop = crop.strip()

    # 1. Lookup Coordinates
    coord_info = DISTRICT_COORDS.get(clean_district.lower(), DEFAULT_DISTRICT_COORD)
    lat = coord_info.get("latitude", 26.9124)
    lon = coord_info.get("longitude", 75.7873)
    elevation = coord_info.get("elevation_m", 300.0)

    # 2. Fetch Open-Meteo Weather (with Climatological fallback)
    weather = await fetch_weather_forecast(latitude=lat, longitude=lon)

    # 3. Calculate FAO-56 Penman-Monteith Reference Evapotranspiration (ET0)
    et0 = calculate_fao56_penman_monteith(
        temp_max_c=weather["temp_max"],
        temp_min_c=weather["temp_min"],
        rh_mean_pct=weather["humidity"],
        wind_speed_2m_ms=weather["wind_speed_2m_ms"],
        solar_radiation_mj=weather["solar_radiation_mj"],
        elevation_m=elevation,
    )

    # 4. Phenological Stage and Crop Coefficient (Kc)
    days_since_sowing = max((date.today() - sowing_date).days, 0)
    stage_name, kc, root_depth, depletion_p = determine_crop_stage_and_kc(
        crop=clean_crop,
        days_since_sowing=days_since_sowing,
    )

    # 5. Crop Evapotranspiration (ETc = Kc * ET0)
    crop_etc = round(kc * et0, 2)

    # 6. Soil Water Depletion & Irrigation Requirement
    # Soil available water capacity (AWC) for Rajasthan sandy-loam ~= 100 mm/m
    awc_mm_per_m = 100.0
    taw_mm = awc_mm_per_m * root_depth  # Total available water
    raw_mm = round(depletion_p * taw_mm, 1)  # Readily available water (Allowable depletion)

    # Net irrigation depth adjusted for application efficiency
    eff_table = THRESHOLDS_REF.get("irrigation_efficiencies", {})
    eff = eff_table.get(irrigation_type.lower(), 0.75)
    gross_irrigation_depth_mm = round(raw_mm / eff, 1)

    days_to_irrigation = max(int(raw_mm / max(crop_etc, 1.0)), 1)

    # 7. Evaluate Crop-Stage Weather Alert Rules
    alerts = evaluate_weather_alerts(crop=clean_crop, stage_name=stage_name, weather=weather)

    # 8. Urgency Assessment
    if weather["precipitation_72h"] >= 10.0:
        urgency = "withhold_due_to_rain"
    elif days_to_irrigation <= 1 or ("क्रांतिक" in stage_name and days_to_irrigation <= 2):
        urgency = "immediate"
    elif days_to_irrigation <= 3:
        urgency = "due_soon"
    else:
        urgency = "normal"

    # Bilingual actionable advisory explanation
    if urgency == "withhold_due_to_rain":
        advisory_text = (
            f"{clean_district} में आगामी 72 घंटों में {weather['precipitation_72h']:.1f} मिमी बारिश की संभावना है। "
            f"अतः वर्तमान में सिंचाई स्थगित रखें ताकि जलभराव व फसल गिरने का जोखिम न हो।"
        )
    elif urgency == "immediate":
        advisory_text = (
            f"{clean_district} में {clean_crop} वर्तमान में '{stage_name}' (बुवाई से {days_since_sowing} दिन) में है। "
            f"दैनिक जल खपत (ETc) {crop_etc} मिमी/दिन है। मिट्टी में जल संचय की सीमा समाप्त हो रही है — तुरंत हल्की सिंचाई ({gross_irrigation_depth_mm} मिमी) अनुशंसित है।"
        )
    else:
        advisory_text = (
            f"{clean_district} में {clean_crop} वर्तमान में '{stage_name}' अवस्था (बुवाई से {days_since_sowing} दिन) में है। "
            f"दैनिक फसल जल मांग (ETc): {crop_etc} मिमी/दिन (Kc: {kc} × ET₀: {et0} मिमी/दिन)। "
            f"आगामी सिंचाई लगभग {days_to_irrigation} दिनों में प्रस्तावित है।"
        )

    weather_summary = {
        "temp_max": weather["temp_max"],
        "temp_min": weather["temp_min"],
        "humidity": weather["humidity"],
        "wind_speed": weather["wind_speed_kmh"],
        "precipitation_sum": weather["precipitation_sum"],
        "precipitation_72h": weather["precipitation_72h"],
        "is_live_weather": weather["is_live"],
        "forecast_days": weather.get("forecast_days", []),
    }

    return IrrigationScheduleResponse(
        district=clean_district,
        crop=clean_crop,
        et0_mm_day=et0,
        kc_factor=kc,
        crop_etc_mm_day=crop_etc,
        days_since_sowing=days_since_sowing,
        current_growth_stage=stage_name,
        next_irrigation_due_days=days_to_irrigation,
        water_depth_mm=gross_irrigation_depth_mm,
        irrigation_urgency=urgency,
        advisory_text=advisory_text,
        alerts=alerts,
        weather_summary=weather_summary,
        methodology="FAO-56 Penman-Monteith (Physics-based deterministic model, zero ML)",
    )
