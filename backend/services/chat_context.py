"""Live structured context for the advisor chat (mandi prices, weather/irrigation, yield).

Price, weather and yield questions cannot be answered from static knowledge-base
passages. This module calls the same services that power the Prices, Weather and
Yield pages and turns their output into numbered source citations plus a compact
structured-data dict for the LLM, so the advisor answers with real numbers.
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.config import get_settings
from app.schemas import SourceCitation
from services.price_service import get_mandi_price_forecast
from services.weather_service import get_irrigation_advisory
from services.yield_service import (
    HISTORICAL_33_DISTRICTS,
    get_district_yield_outlook,
)

logger = logging.getLogger("kisansathi.chat_context")
settings = get_settings()

# Hindi spellings for frequently asked districts
_HINDI_DISTRICTS = {
    "जयपुर": "Jaipur", "कोटा": "Kota", "अलवर": "Alwar", "बीकानेर": "Bikaner",
    "जोधपुर": "Jodhpur", "उदयपुर": "Udaipur", "अजमेर": "Ajmer", "भरतपुर": "Bharatpur",
    "सीकर": "Sikar", "नागौर": "Nagaur", "टोंक": "Tonk", "पाली": "Pali",
    "झालावाड़": "Jhalawar", "बारां": "Baran", "बूंदी": "Bundi", "चूरू": "Churu",
    "हनुमानगढ़": "Hanumangarh", "श्रीगंगानगर": "Sri Ganganagar", "दौसा": "Dausa",
    "भीलवाड़ा": "Bhilwara", "चित्तौड़गढ़": "Chittorgarh", "बाड़मेर": "Barmer",
    "जैसलमेर": "Jaisalmer", "झुंझुनू": "Jhunjhunu", "सवाई माधोपुर": "Sawai Madhopur",
}

_WEATHER_WORDS = (
    "rain", "weather", "temperature", "forecast", "frost", "irrigat", "water", "heat",
    "मौसम", "बारिश", "वर्षा", "तापमान", "पाला", "सिंचाई", "पानी", "पाणी",
)


def detect_district(question: str) -> Optional[str]:
    """Return a district named in the question, if any."""
    q = question.lower()
    for hi, en in _HINDI_DISTRICTS.items():
        if hi in question:
            return en
    for d in sorted(HISTORICAL_33_DISTRICTS, key=len, reverse=True):
        if d.lower() in q:
            return d
    return None


def _crop_known(profile: Dict[str, Any]) -> Optional[str]:
    crop = profile.get("crop")
    return crop if crop and crop != "-" else None


async def build_structured_context(
    intent: str,
    question: str,
    profile: Dict[str, Any],
    detected_crop: Optional[str],
    language: str,
    db: Optional[Session],
) -> Tuple[Dict[str, Any], List[SourceCitation]]:
    """Collect live data relevant to the intent. Never raises; returns ({}, []) on failure."""
    data: Dict[str, Any] = {}
    citations: List[SourceCitation] = []
    q = question.lower()
    crop = detected_crop or _crop_known(profile)
    district = detect_district(question) or (
        profile.get("district") if profile.get("district") not in (None, "-", "Rajasthan") else None
    )

    try:
        if intent == "price" and crop:
            mandi = district or "Jaipur"
            forecast = get_mandi_price_forecast(mandi=mandi, commodity=crop, days=30, db=db)
            data["mandi_price"] = {
                "mandi": forecast.mandi,
                "commodity": forecast.commodity,
                "latest_date": str(forecast.latest_date),
                "latest_modal_price_rs_per_quintal": forecast.latest_modal_price,
                "trend": forecast.trend,
                "forecast_2_weeks_rs": forecast.forecast_2_weeks.model_dump(),
                "forecast_4_weeks_rs": forecast.forecast_4_weeks.model_dump(),
                "recommendation": forecast.recommendation_text or forecast.recommendation,
                "model_version": forecast.model_version,
            }
            citations.append(SourceCitation(
                doc_title=f"Mandi price: {forecast.commodity} at {forecast.mandi}",
                source=f"APMC/Agmarknet records (forecast model: {forecast.model_version})",
                chunk_text=(
                    f"Latest modal price on {forecast.latest_date}: Rs {forecast.latest_modal_price:.0f}/quintal. "
                    f"Trend: {forecast.trend}. 2-week range Rs {forecast.forecast_2_weeks.min_expected:.0f}-"
                    f"{forecast.forecast_2_weeks.max_expected:.0f}. {forecast.explanation}"
                ),
                relevance_score=0.95,
            ))

        elif (
            settings.ENVIRONMENT != "test"  # avoid live weather network calls in unit tests
            and intent in ("weather", "yield", "general")
            and any(w in q for w in _WEATHER_WORDS)
        ):
            sowing = profile.get("sowing_date")
            profile_crop = _crop_known(profile)
            same_crop = not detected_crop or (profile_crop and detected_crop.lower() == profile_crop.lower())
            if sowing and sowing != "-" and profile_crop and same_crop:
                sow_date = date.fromisoformat(str(sowing)) if not isinstance(sowing, date) else sowing
                advisory = await get_irrigation_advisory(
                    district=district or profile.get("district") or "Jaipur",
                    crop=profile_crop,
                    sowing_date=sow_date,
                    irrigation_type=profile.get("irrigation") if profile.get("irrigation") != "-" else "tubewell",
                )
                data["weather_irrigation"] = {
                    "district": advisory.district,
                    "crop": advisory.crop,
                    "growth_stage": advisory.current_growth_stage,
                    "days_since_sowing": advisory.days_since_sowing,
                    "next_irrigation_due_in_days": advisory.next_irrigation_due_days,
                    "irrigation_urgency": advisory.irrigation_urgency,
                    "water_depth_mm": advisory.water_depth_mm,
                    "advisory": advisory.advisory_text,
                    "weather": advisory.weather_summary,
                    "alerts": [a.message for a in advisory.alerts],
                }
                citations.append(SourceCitation(
                    doc_title=f"Weather & irrigation advisory: {advisory.crop}, {advisory.district}",
                    source="Open-Meteo forecast + FAO-56 Penman-Monteith (deterministic)",
                    chunk_text=(
                        f"Stage: {advisory.current_growth_stage} ({advisory.days_since_sowing} days after sowing). "
                        f"Next irrigation in {advisory.next_irrigation_due_days} days "
                        f"({advisory.water_depth_mm:.0f} mm). {advisory.advisory_text}"
                    ),
                    relevance_score=0.95,
                ))

        if intent == "yield" and crop:
            outlook = get_district_yield_outlook(
                district=district or profile.get("district") or "Jaipur",
                crop=crop,
                season="Kharif" if crop.lower() in ("bajra", "soybean", "guar", "moong", "cotton") else "Rabi",
                forecast_year=datetime.now().year,
                language="en",
            )
            data["yield_outlook"] = {
                "district": outlook.district,
                "crop": outlook.crop,
                "expected_yield_kg_per_ha": outlook.predicted_yield_kg_ha,
                "five_year_mean_kg_per_ha": outlook.baseline_5yr_mean_kg_ha,
                "model_version": outlook.model_version,
            }
            citations.append(SourceCitation(
                doc_title=f"Yield outlook: {outlook.crop}, {outlook.district}",
                source=f"District yield series (estimate type: {outlook.model_version})",
                chunk_text=outlook.summary_text,
                relevance_score=0.9,
            ))
    except LookupError:
        pass
    except Exception as exc:  # live data must never break the advisor
        logger.warning("Structured context for intent '%s' unavailable: %s", intent, exc)
        if db is not None:
            try:
                db.rollback()
            except Exception:
                pass

    return data, citations
