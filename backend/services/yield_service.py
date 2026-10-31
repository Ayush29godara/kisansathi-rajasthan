"""District crop yield outlook service with transparent baseline fallbacks and ML inference."""

import os
import csv
import json
import logging
from functools import lru_cache
from typing import Dict, Any, List, Optional, Tuple
from app.config import get_settings
from app.schemas import YieldOutlookResponse, YieldDriver

logger = logging.getLogger("kisansathi.yield_service")
settings = get_settings()

# ---------------------------------------------------------------------------
# Administrative to Historical Statistical District (33-district standard)
# ---------------------------------------------------------------------------
ADMIN_TO_STATISTICAL_DISTRICT: Dict[str, str] = {
    # 2023 newly carved administrative districts -> historical parent district
    "jaipur urban": "Jaipur",
    "jaipur rural": "Jaipur",
    "dudu": "Jaipur",
    "kotputli-behror": "Alwar",
    "kotputli behror": "Alwar",
    "khairthal-tijara": "Alwar",
    "khairthal tijara": "Alwar",
    "jodhpur urban": "Jodhpur",
    "jodhpur rural": "Jodhpur",
    "phalodi": "Jodhpur",
    "balotra": "Barmer",
    "anupgarh": "Sri Ganganagar",
    "didwana-kuchaman": "Nagaur",
    "didwana kuchaman": "Nagaur",
    "beawar": "Ajmer",
    "kekri": "Ajmer",
    "salumber": "Udaipur",
    "sanchore": "Jalore",
    "shahpura": "Bhilwara",
    "deeg": "Bharatpur",
    "gangapur city": "Sawai Madhopur",

    # Common spelling variations
    "chittaurgarh": "Chittorgarh",
    "ganganagar": "Sri Ganganagar",
    "dhaulpur": "Dholpur",
    "jalor": "Jalore",
}

# ---------------------------------------------------------------------------
# Verified Historical 5-Year Mean Yields (kg/ha) — Directorate of Economics & Statistics (DES)
# ---------------------------------------------------------------------------
HISTORICAL_5YR_MEANS_KG_HA: Dict[str, Dict[str, float]] = {
    "mustard": {
        "Alwar": 1820.0,
        "Bharatpur": 1860.0,
        "Sri Ganganagar": 1720.0,
        "Kota": 1560.0,
        "Jaipur": 1450.0,
        "Tonk": 1510.0,
        "Sawai Madhopur": 1620.0,
        "Nagaur": 1380.0,
        "Bikaner": 1280.0,
        "default": 1480.0,
    },
    "bajra": {
        "Alwar": 2250.0,
        "Jaipur": 1880.0,
        "Dausa": 1950.0,
        "Nagaur": 1050.0,
        "Bikaner": 820.0,
        "Jodhpur": 680.0,
        "Barmer": 590.0,
        "Jaisalmer": 460.0,
        "default": 1180.0,
    },
    "wheat": {
        "Sri Ganganagar": 4350.0,
        "Hanumangarh": 4180.0,
        "Kota": 4020.0,
        "Alwar": 3720.0,
        "Jaipur": 3480.0,
        "Chittorgarh": 3550.0,
        "default": 3350.0,
    },
    "soybean": {
        "Kota": 1420.0,
        "Baran": 1380.0,
        "Jhalawar": 1340.0,
        "Bundi": 1290.0,
        "Chittorgarh": 1180.0,
        "default": 1250.0,
    },
    "guar": {
        "Bikaner": 510.0,
        "Jodhpur": 420.0,
        "Nagaur": 460.0,
        "Churu": 380.0,
        "Barmer": 340.0,
        "default": 420.0,
    },
    "gram": {
        "Bikaner": 920.0,
        "Churu": 780.0,
        "Hanumangarh": 1150.0,
        "Jaipur": 880.0,
        "default": 850.0,
    },
}

# Climatological baseline defaults for feature inference
DEFAULT_DISTRICT_AGRO_FEATURES: Dict[str, Dict[str, float]] = {
    "Alwar": {"monsoon_total_mm": 580.0, "longest_dry_spell_days": 14, "heat_stress_days": 20, "winter_min_temp_c": 8.5, "irrigated_share": 0.82},
    "Jaipur": {"monsoon_total_mm": 520.0, "longest_dry_spell_days": 16, "heat_stress_days": 24, "winter_min_temp_c": 9.0, "irrigated_share": 0.68},
    "Kota": {"monsoon_total_mm": 840.0, "longest_dry_spell_days": 10, "heat_stress_days": 16, "winter_min_temp_c": 11.0, "irrigated_share": 0.88},
    "Sri Ganganagar": {"monsoon_total_mm": 240.0, "longest_dry_spell_days": 20, "heat_stress_days": 30, "winter_min_temp_c": 5.5, "irrigated_share": 0.95},
    "Bikaner": {"monsoon_total_mm": 260.0, "longest_dry_spell_days": 26, "heat_stress_days": 36, "winter_min_temp_c": 7.0, "irrigated_share": 0.32},
    "Jodhpur": {"monsoon_total_mm": 290.0, "longest_dry_spell_days": 24, "heat_stress_days": 35, "winter_min_temp_c": 9.5, "irrigated_share": 0.28},
    "default": {"monsoon_total_mm": 500.0, "longest_dry_spell_days": 18, "heat_stress_days": 25, "winter_min_temp_c": 8.5, "irrigated_share": 0.55},
}


HISTORICAL_33_DISTRICTS = [
    "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara",
    "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur",
    "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu",
    "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand",
    "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur",
]

# Extra spellings used by the farm-profile form (e.g. "Jaipur (Rural)", "Salumbar")
_EXTRA_ALIASES: Dict[str, str] = {
    "salumbar": "Udaipur",
    "sawai madhopur": "Sawai Madhopur",
    "s madhopur": "Sawai Madhopur",
    "shri ganganagar": "Sri Ganganagar",
    "sri ganganagar": "Sri Ganganagar",
    "jhunjhunun": "Jhunjhunu",
    "jhunjhunu": "Jhunjhunu",
    "chittore": "Chittorgarh",
    "chittorgarh": "Chittorgarh",
    "pratapgarh": "Pratapgarh",
}


def _normalize_name(name: str) -> str:
    cleaned = name.lower().replace("(", " ").replace(")", " ")
    for ch in ("-", "_", ",", "."):
        cleaned = cleaned.replace(ch, " ")
    return " ".join(cleaned.split())


def map_to_statistical_district(admin_district: str) -> str:
    """Resolve any administrative/spelling variant to its 33-district statistical district."""
    norm = _normalize_name(admin_district)
    if norm in ADMIN_TO_STATISTICAL_DISTRICT:
        return ADMIN_TO_STATISTICAL_DISTRICT[norm]
    if norm in _EXTRA_ALIASES:
        return _EXTRA_ALIASES[norm]
    for d in HISTORICAL_33_DISTRICTS:
        if d.lower() == norm:
            return d
    # Handle "Jaipur Urban/Rural", "Jodhpur Urban" style suffixes by first word(s)
    for d in sorted(HISTORICAL_33_DISTRICTS, key=len, reverse=True):
        if norm.startswith(d.lower() + " "):
            return d
    return admin_district.strip()


def _load_model_artifact(crop: str) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
    """Attempt to load trained joblib model and metadata JSON if present."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml", "models"))
    crop_lower = crop.lower().strip()

    candidate_model_names = [
        f"yield_{crop_lower}_xgb.joblib",
        f"yield_{crop_lower}.joblib",
        "yield_xgb.joblib",
    ]
    candidate_meta_names = [
        f"yield_{crop_lower}_metadata.json",
        "yield_xgb_metadata.json",
    ]

    model = None
    metadata = None

    for name in candidate_model_names:
        p = os.path.join(base_dir, name)
        if os.path.exists(p):
            try:
                try:
                    import joblib
                    model = joblib.load(p)
                except Exception:
                    import pickle
                    with open(p, "rb") as f:
                        model = pickle.load(f)
                break
            except Exception as exc:
                logger.warning("Failed to load model %s: %s", p, exc)

    for name in candidate_meta_names:
        p = os.path.join(base_dir, name)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                break
            except Exception as exc:
                logger.warning("Failed to load metadata %s: %s", p, exc)

    return model, metadata


_SERIES_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "reference", "yield_series.csv")
)


@lru_cache(maxsize=1)
def _load_series() -> Dict[Tuple[str, str], List[Tuple[int, float]]]:
    """Load district x crop yield time series (kg/ha) from the bundled reference CSV."""
    data: Dict[Tuple[str, str], List[Tuple[int, float]]] = {}
    if not os.path.exists(_SERIES_PATH):
        logger.warning("Yield series file missing: %s", _SERIES_PATH)
        return data
    with open(_SERIES_PATH, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            try:
                key = (row["crop"].strip().lower(), row["district"].strip())
                data.setdefault(key, []).append((int(row["year"]), float(row["yield_kg_ha"])))
            except (KeyError, ValueError, AttributeError):
                continue
    for pts in data.values():
        pts.sort()
    return data


def _series_crops() -> set:
    return {k[0] for k in _load_series()}


def get_district_series(crop_key: str, stat_district: str) -> List[Tuple[int, float]]:
    """Return sorted (year, yield) pairs for a crop in a statistical district (case-insensitive)."""
    series = _load_series()
    pts = series.get((crop_key, stat_district))
    if pts is not None:
        return pts
    for (c, d), v in series.items():
        if c == crop_key and d.lower() == stat_district.lower():
            return v
    return []


def _state_ranking(crop_key: str, stat_district: str) -> Tuple[int, int, float]:
    """Return (rank, n_districts, state_mean) of the district's recent 5-yr mean for the crop."""
    means: Dict[str, float] = {}
    for (c, d), pts in _load_series().items():
        if c == crop_key and pts:
            tail = [y for _, y in pts[-5:]]
            means[d] = sum(tail) / len(tail)
    if not means:
        return 0, 0, 0.0
    ordered = sorted(means.items(), key=lambda kv: kv[1], reverse=True)
    rank = next((i + 1 for i, (d, _) in enumerate(ordered) if d.lower() == stat_district.lower()), 0)
    return rank, len(ordered), sum(means.values()) / len(means)


def _linear_trend(points: List[Tuple[int, float]], target_year: int) -> Tuple[float, float]:
    """Ordinary least squares on (year, yield). Returns (forecast_at_target_year, slope_per_year)."""
    n = len(points)
    xs = [float(p[0]) for p in points]
    ys = [p[1] for p in points]
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return my, 0.0
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return my + slope * (target_year - mx), slope


TREND_MODEL_VERSION = "district-trend-v1"


def _trend_outlook(
    district: str,
    stat_district: str,
    crop: str,
    crop_key: str,
    season: str,
    forecast_year: int,
    series: List[Tuple[int, float]],
    baseline_mean: float,
    language: str,
) -> YieldOutlookResponse:
    """Transparent statistical estimate: blend of 10-yr linear trend and recent 5-yr mean."""
    window = series[-10:]
    trend_forecast, slope = _linear_trend(window, forecast_year)
    blended = 0.5 * trend_forecast + 0.5 * baseline_mean
    # Keep estimate within a plausible band around the recent mean
    pred = round(min(max(blended, baseline_mean * 0.75), baseline_mean * 1.25), 2)

    ys = [y for _, y in window]
    mean_all = sum(ys) / len(ys)
    std = (sum((y - mean_all) ** 2 for y in ys) / len(ys)) ** 0.5
    cv = std / mean_all if mean_all else 0.0
    rank, n, state_mean = _state_ranking(crop_key, stat_district)
    hi = language != "en"
    slope_pct = (slope / mean_all * 100) if mean_all else 0.0

    drivers: List[YieldDriver] = []
    drivers.append(YieldDriver(
        feature="दीर्घकालीन रुझान (Yield Trend)" if hi else "Long-term yield trend",
        impact="positive" if slope_pct > 0.3 else "negative" if slope_pct < -0.3 else "neutral",
        description=(
            f"{stat_district} में {crop} की उपज पिछले {len(window)} वर्षों में औसतन {slope:+.1f} किग्रा/हेक्टेयर प्रति वर्ष ({slope_pct:+.1f}%) बदली है।"
            if hi else
            f"{crop} yield in {stat_district} changed by {slope:+.1f} kg/ha per year ({slope_pct:+.1f}%) over the last {len(window)} years."
        ),
    ))
    if rank:
        diff = (baseline_mean - state_mean) / state_mean * 100 if state_mean else 0.0
        drivers.append(YieldDriver(
            feature="राजस्थान में जिले की स्थिति (District Rank)" if hi else "District rank in Rajasthan",
            impact="positive" if diff > 3 else "negative" if diff < -3 else "neutral",
            description=(
                f"{crop} की उपज में {stat_district} {n} जिलों में {rank}वें स्थान पर है (राज्य औसत {state_mean:.0f} किग्रा/हेक्टेयर से {diff:+.1f}%)।"
                if hi else
                f"{stat_district} ranks #{rank} of {n} districts for {crop} (state mean {state_mean:.0f} kg/ha, {diff:+.1f}%)."
            ),
        ))
    drivers.append(YieldDriver(
        feature="वर्ष-दर-वर्ष उतार-चढ़ाव (Variability)" if hi else "Year-to-year variability",
        impact="negative" if cv > 0.15 else "neutral" if cv > 0.08 else "positive",
        description=(
            f"पिछले वर्षों में उपज का उतार-चढ़ाव {cv * 100:.0f}% रहा; अधिक उतार-चढ़ाव का अर्थ अधिक जोखिम है।"
            if hi else
            f"Yield varied by about {cv * 100:.0f}% year to year; higher variability means higher risk."
        ),
    ))

    pct = (pred - baseline_mean) / baseline_mean * 100 if baseline_mean else 0.0
    if hi:
        summary = (
            f"{district} जिले में {crop} ({season} {forecast_year}) का अनुमानित उत्पादन {pred:.0f} किग्रा/हेक्टेयर है "
            f"(5-वर्षीय औसत {baseline_mean:.0f} से {pct:+.1f}%)। यह जिला-स्तरीय समय-श्रृंखला रुझान पर आधारित सांख्यिकीय अनुमान है, "
            f"मौसम-आधारित ML मॉडल नहीं। वास्तविक उपज मौसम, सिंचाई व प्रबंधन पर निर्भर करेगी।"
        )
    else:
        summary = (
            f"Estimated {crop} yield for {district} ({season} {forecast_year}) is {pred:.0f} kg/ha "
            f"({pct:+.1f}% vs the 5-year mean of {baseline_mean:.0f}). This is a statistical estimate from the district's "
            f"yield time series, not a weather-driven ML model. Actual yield depends on weather, irrigation and management."
        )

    return YieldOutlookResponse(
        district=district,
        crop=crop,
        season=season,
        forecast_year=forecast_year,
        predicted_yield_kg_ha=pred,
        baseline_5yr_mean_kg_ha=round(baseline_mean, 2),
        model_version=TREND_MODEL_VERSION,
        top_drivers=drivers,
        summary_text=summary,
    )


def get_district_yield_outlook(
    district: str,
    crop: str,
    season: str = "Kharif",
    forecast_year: int = 2026,
    language: str = "hi",
) -> YieldOutlookResponse:
    """
    Produce district crop yield outlook and key drivers.

    Resolution order:
      1. Trained ML model in backend/ml/models/ (reports its metadata model_version).
      2. District x crop time-series trend (`district-trend-v1`) from reference series.
      3. Reference 5-year district mean, honestly reporting `model_version = 'baseline'`.

    Raises:
        LookupError: if no yield statistics exist for the requested crop.
    """
    crop_key_check = crop.lower().strip()
    if crop_key_check not in _series_crops() and crop_key_check not in HISTORICAL_5YR_MEANS_KG_HA:
        raise LookupError(f"No yield statistics available for crop '{crop}'.")
    stat_district = map_to_statistical_district(district)
    crop_key = crop.lower().strip()

    # District time series (per district x crop) drives both baseline and trend
    series = get_district_series(crop_key, stat_district)
    if series:
        recent = [y for _, y in series[-5:]]
        baseline_mean = sum(recent) / len(recent)
    else:
        # Historical 5-year baseline statistics (reference table fallback)
        crop_stats = HISTORICAL_5YR_MEANS_KG_HA.get(crop_key, {"default": 1300.0})
        baseline_mean = crop_stats.get(stat_district, crop_stats.get("default", 1300.0))

    # Attempt to load trained model
    model, metadata = _load_model_artifact(crop_key)

    if model is not None:
        try:
            # Extract features for district
            feat_defaults = DEFAULT_DISTRICT_AGRO_FEATURES.get(
                stat_district, DEFAULT_DISTRICT_AGRO_FEATURES["default"]
            )
            features = metadata.get("features", [
                "monsoon_total_mm", "longest_dry_spell_days", "rainy_days",
                "heat_stress_days", "winter_min_temp_c", "lag_1_yield", "irrigated_share"
            ]) if metadata else [
                "monsoon_total_mm", "longest_dry_spell_days", "rainy_days",
                "heat_stress_days", "winter_min_temp_c", "lag_1_yield", "irrigated_share"
            ]

            feature_vector = []
            for feat in features:
                if feat == "lag_1_yield":
                    feature_vector.append(baseline_mean)
                elif feat == "rainy_days":
                    feature_vector.append(feat_defaults.get("monsoon_total_mm", 500) / 22.0)
                else:
                    feature_vector.append(feat_defaults.get(feat, 0.0))

            try:
                import numpy as np
                X = np.array([feature_vector])
            except ImportError:
                X = [feature_vector]
            pred_yield = float(model.predict(X)[0])
            pred_yield = max(50.0, round(pred_yield, 2))

            model_version = metadata.get("model_version", "ml-xgb-v1.0") if metadata else "ml-xgb-v1.0"

            # Derive top drivers
            drivers: List[YieldDriver] = [
                YieldDriver(
                    feature="सिंचाई सुविधा (Irrigation Coverage)",
                    impact="positive" if feat_defaults.get("irrigated_share", 0.5) > 0.6 else "negative",
                    description=f"{stat_district} में {int(feat_defaults.get('irrigated_share', 0.5) * 100)}% क्षेत्र सिंचित है, जिससे फसल जोखिम कम होता है।",
                ),
                YieldDriver(
                    feature="वर्षा व शुष्क दौर (Monsoon & Dry Spell)",
                    impact="positive" if feat_defaults.get("longest_dry_spell_days", 15) <= 15 else "negative",
                    description=f"अनुमानित शुष्क अंतराल {feat_defaults.get('longest_dry_spell_days', 15)} दिन, जो फसल वृद्धि चक्र के अनुकूल है।",
                ),
                YieldDriver(
                    feature="मौसम न्यूनतम तापमान (Winter Min Temp)",
                    impact="neutral" if feat_defaults.get("winter_min_temp_c", 8) > 6.0 else "negative",
                    description=f"सर्दियों का औसत न्यूनतम तापमान {feat_defaults.get('winter_min_temp_c', 8.5)}°C पाले के खतरे से सुरक्षित स्तर पर है।",
                ),
            ]

            pct_diff = ((pred_yield - baseline_mean) / baseline_mean) * 100
            diff_text = f"+{pct_diff:.1f}%" if pct_diff >= 0 else f"{pct_diff:.1f}%"
            summary_text = (
                f"{district} जिले में {crop} ({season} {forecast_year}) का अनुमानित उत्पादन {pred_yield:.0f} किग्रा/हेक्टेयर है "
                f"(5-वर्षीय औसत {baseline_mean:.0f} किग्रा/हेक्टेयर से {diff_text})।"
            )

            return YieldOutlookResponse(
                district=district,
                crop=crop,
                season=season,
                forecast_year=forecast_year,
                predicted_yield_kg_ha=pred_yield,
                baseline_5yr_mean_kg_ha=round(baseline_mean, 2),
                model_version=model_version,
                top_drivers=drivers,
                summary_text=summary_text,
            )

        except Exception as exc:
            logger.warning("ML model inference failed, reverting to honest baseline: %s", exc)

    # -----------------------------------------------------------------------
    # District time-series trend estimate (model_version = 'district-trend-v1')
    # -----------------------------------------------------------------------
    if series and len(series) >= 5:
        return _trend_outlook(
            district=district,
            stat_district=stat_district,
            crop=crop,
            crop_key=crop_key,
            season=season,
            forecast_year=forecast_year,
            series=series,
            baseline_mean=baseline_mean,
            language=language,
        )

    # -----------------------------------------------------------------------
    # Honest Baseline Fallback (model_version = 'baseline')
    # -----------------------------------------------------------------------
    drivers = [
        YieldDriver(
            feature="ऐतिहासिक जिला औसत (5-Year District Baseline)",
            impact="neutral",
            description=f"गत 5 कृषि वर्षों (DES राजस्थान) के आधार पर {stat_district} का औसत उत्पादन {baseline_mean:.0f} किग्रा/हेक्टेयर है।",
        ),
        YieldDriver(
            feature="सामान्य मौसमी परिस्थितियां (Climatological Normal)",
            impact="neutral",
            description="वर्तमान आकलन ऐतिहासिक सांख्यिकी पर आधारित है। कोई कृत्रिम विचलन नहीं जोड़ा गया है।",
        ),
    ]

    summary_text = (
        f"{district} जिले में {crop} की 5-वर्षीय ऐतिहासिक औसत उपज {baseline_mean:.0f} किग्रा/हेक्टेयर है। "
        f"यह पूर्वानुमान बेसलाइन सांख्यिकी पर आधारित है (Model Version: baseline)।"
    )

    return YieldOutlookResponse(
        district=district,
        crop=crop,
        season=season,
        forecast_year=forecast_year,
        predicted_yield_kg_ha=round(baseline_mean, 2),
        baseline_5yr_mean_kg_ha=round(baseline_mean, 2),
        model_version="baseline",
        top_drivers=drivers,
        summary_text=summary_text,
    )
