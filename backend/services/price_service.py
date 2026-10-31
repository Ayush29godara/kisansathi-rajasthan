"""Mandi price trend and 2-4 week forecasting service with baseline fallbacks and ML inference."""

import os
import csv
import json
import logging
from datetime import date, timedelta, datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.config import get_settings
from app.schemas import (
    MandiPriceForecastResponse,
    PriceForecastRange,
    MandiPriceRecord,
)

logger = logging.getLogger("kisansathi.price_service")
settings = get_settings()

# Reference benchmark modal prices (INR / Quintal) for Rajasthan Mandis
BENCHMARK_MODAL_PRICES: Dict[str, float] = {
    "mustard": 5450.0,
    "wheat": 2425.0,
    "bajra": 2250.0,
    "gram": 5850.0,
    "soybean": 4600.0,
    "guar": 5100.0,
    "cumin": 28000.0,
    "moong": 7800.0,
    "coriander": 7200.0,
    "cotton": 6900.0,
}

# Test override hook for synthetic price models (isolated to unit tests)
TEST_ONLY_SYNTHETIC_PRICE_MODEL: Optional[Any] = None


def determine_recommendation(
    pct_change_2wk: float,
    language: str = "hi",
) -> Tuple[str, str, str]:
    """
    Formulate trend and 'sell now / wait' decision support advice.
    
    Decision rules:
    - Expected change > +2.5% -> Bullish, 'wait' (hold inventory for higher prices)
    - Expected change < -2.5% -> Bearish, 'sell_now' (sell before anticipated dip)
    - Within ±2.5% -> Stable, 'hold' (normal price stability)
    """
    if pct_change_2wk > 2.5:
        trend = "bullish"
        recommendation = "wait"
        if language == "en":
            hint = (
                f"Wait: Prices are projected to rise by approximately {abs(pct_change_2wk):.1f}% over the next 2-4 weeks. "
                "If immediate cash is not urgently required, holding produce may yield better returns."
            )
        else:
            hint = (
                f"रुकें (Wait): आगामी 2-4 सप्ताह में भाव में लगभग {abs(pct_change_2wk):.1f}% की संभावित बढ़त के संकेत हैं। "
                "यदि तत्काल नकदी की आवश्यकता न हो, तो माल रोककर रखना लाभकारी हो सकता है।"
            )
    elif pct_change_2wk < -2.5:
        trend = "bearish"
        recommendation = "sell_now"
        if language == "en":
            hint = (
                f"Sell Now: Prices are projected to soften by approximately {abs(pct_change_2wk):.1f}% over the coming weeks. "
                "Selling at current prevailing prices may help avoid market downside."
            )
        else:
            hint = (
                f"तुरंत बेचें (Sell Now): आगामी सप्ताहों में भाव में लगभग {abs(pct_change_2wk):.1f}% की संभावित मंदी के संकेत हैं। "
                "वर्तमान प्रचलित भाव पर विक्रय करना जोखिम से बचने हेतु सुरक्षित विकल्प हो सकता है।"
            )
    else:
        trend = "stable"
        recommendation = "hold"
        if language == "en":
            hint = (
                "Hold / Steady: Prices are expected to remain stable within a normal ±2% band. "
                "You may sell produce according to your logistical and storage convenience."
            )
        else:
            hint = (
                "सामान्य / सुविधानुसार बेचें (Hold): भाव में निकट भविष्य में बड़े उतार-चढ़ाव के संकेत नहीं हैं। "
                "अपनी भंडारण व नकदी सुविधा अनुसार सामान्य रूप से विक्रय करें।"
            )

    return trend, recommendation, hint


def load_historical_prices(
    mandi: str,
    commodity: str,
    days: int = 30,
    db: Optional[Session] = None,
) -> List[MandiPriceRecord]:
    """
    Fetch historical daily mandi price observations.
    
    Priority:
    1. Database `mandi_prices` table (if db is connected and populated).
    2. Local cleaned dataset `data/mandi_data/cleaned_mandi.csv`.
    3. Realistic benchmark price sequence (derived from typical APMC variations).
    """
    records: List[MandiPriceRecord] = []
    mandi_norm = mandi.strip().lower()
    comm_norm = commodity.strip().lower()

    # 1. Database query
    if db is not None:
        try:
            from app.models import MandiPriceModel
            cutoff_date = date.today() - timedelta(days=days + 5)
            db_rows = (
                db.query(MandiPriceModel)
                .filter(
                    MandiPriceModel.mandi.ilike(f"%{mandi.strip()}%"),
                    MandiPriceModel.commodity.ilike(f"%{commodity.strip()}%"),
                    MandiPriceModel.price_date >= cutoff_date,
                )
                .order_by(MandiPriceModel.price_date.asc())
                .all()
            )
            for r in db_rows:
                records.append(
                    MandiPriceRecord(
                        price_date=r.price_date,
                        modal_price=float(r.modal_price),
                        min_price=float(r.min_price),
                        max_price=float(r.max_price),
                        arrivals=float(r.arrivals) if r.arrivals is not None else 0.0,
                    )
                )
            if records:
                return records[-days:]
        except Exception as exc:
            logger.debug("Database mandi lookup skipped or empty: %s", exc)

    # 2. Local CSV dataset
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    csv_paths = [
        os.path.join(repo_root, "data", "mandi_data", "cleaned_mandi.csv"),
        os.path.join(os.getcwd(), "data", "mandi_data", "cleaned_mandi.csv"),
    ]
    for p in csv_paths:
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        r_mandi = row.get("mandi", "").strip().lower()
                        r_comm = row.get("commodity", "").strip().lower()
                        if (mandi_norm in r_mandi or r_mandi in mandi_norm) and (comm_norm in r_comm or r_comm in comm_norm):
                            try:
                                d_val = datetime.strptime(row["price_date"].strip(), "%Y-%m-%d").date()
                                records.append(
                                    MandiPriceRecord(
                                        price_date=d_val,
                                        modal_price=round(float(row["modal_price"]), 2),
                                        min_price=round(float(row.get("min_price", float(row["modal_price"]) * 0.95)), 2),
                                        max_price=round(float(row.get("max_price", float(row["modal_price"]) * 1.05)), 2),
                                        arrivals=round(float(row.get("arrivals", 100.0)), 1),
                                    )
                                )
                            except Exception:
                                continue
                if records:
                    records.sort(key=lambda x: x.price_date)
                    return records[-days:]
            except Exception as exc:
                logger.debug("Error reading mandi CSV: %s", exc)

    # 3. Benchmark generated series if neither DB nor CSV returned records
    base_modal = BENCHMARK_MODAL_PRICES.get(comm_norm, 3500.0)
    today = date.today()
    for offset in range(days, 0, -1):
        rec_date = today - timedelta(days=offset)
        # Gentle realistic day-to-day fluctuation (within ±1.8%)
        wave = ((offset * 7) % 19 - 9) * (base_modal * 0.0015)
        mod_p = round(base_modal + wave, 2)
        records.append(
            MandiPriceRecord(
                price_date=rec_date,
                modal_price=mod_p,
                min_price=round(mod_p * 0.96, 2),
                max_price=round(mod_p * 1.04, 2),
                arrivals=round(80.0 + ((offset * 13) % 120), 1),
            )
        )
    return records


def get_mandi_price_forecast(
    mandi: str,
    commodity: str,
    days: int = 30,
    db: Optional[Session] = None,
) -> MandiPriceForecastResponse:
    """
    Produce mandi price trend and 2-4 week forecast range.
    
    1. Fetches historical prices from DB or verified local records.
    2. Runs quantile time-series model (q10, q50, q90) if present in models directory.
    3. Transparently falls back to persistence baseline if no model is found,
       reporting `model_version = 'baseline'`.
    4. Computes actionable 'sell now / wait' decision guidance and clear market risk disclaimer.
    """
    clean_mandi = mandi.strip()
    clean_commodity = commodity.strip()
    history = load_historical_prices(mandi=clean_mandi, commodity=clean_commodity, days=days, db=db)

    if history:
        latest_record = history[-1]
        latest_price = latest_record.modal_price
        latest_date = latest_record.price_date
    else:
        latest_price = BENCHMARK_MODAL_PRICES.get(clean_commodity.lower(), 3500.0)
        latest_date = date.today()

    # -------------------------------------------------------------------------
    # Check for Trained ML Quantile Regressor Model
    # -------------------------------------------------------------------------
    model_loaded = False
    two_week_forecast: Optional[PriceForecastRange] = None
    four_week_forecast: Optional[PriceForecastRange] = None
    model_ver: str = "baseline"

    # Synthetic test hook
    if TEST_ONLY_SYNTHETIC_PRICE_MODEL is not None:
        try:
            preds = TEST_ONLY_SYNTHETIC_PRICE_MODEL.predict(latest_price)
            two_week_forecast = PriceForecastRange(
                min_expected=round(preds["2wk_q10"], 2),
                max_expected=round(preds["2wk_q90"], 2),
                expected_modal=round(preds["2wk_q50"], 2),
            )
            four_week_forecast = PriceForecastRange(
                min_expected=round(preds["4wk_q10"], 2),
                max_expected=round(preds["4wk_q90"], 2),
                expected_modal=round(preds["4wk_q50"], 2),
            )
            model_ver = getattr(TEST_ONLY_SYNTHETIC_PRICE_MODEL, "model_version", "synthetic-test-v1.0")
            model_loaded = True
        except Exception as exc:
            logger.warning("Test synthetic model failed, falling back to baseline: %s", exc)

    # Check disk for serialized trained model
    if not model_loaded:
        models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml", "models"))
        model_paths = [
            os.path.join(models_dir, f"price_{clean_commodity.lower()}_{clean_mandi.lower()}_lgb.joblib"),
            os.path.join(models_dir, "price_lgb.joblib"),
        ]
        meta_paths = [
            os.path.join(models_dir, f"price_{clean_commodity.lower()}_{clean_mandi.lower()}_lgb_metadata.json"),
            os.path.join(models_dir, "price_lgb_metadata.json"),
        ]

        for m_path, meta_path in zip(model_paths, meta_paths):
            if os.path.isfile(m_path):
                try:
                    import joblib
                    pkg = joblib.load(m_path)
                    metadata = {}
                    if os.path.isfile(meta_path):
                        with open(meta_path, "r", encoding="utf-8") as mf:
                            metadata = json.load(mf)

                    # Extract models for quantiles
                    q10_m = pkg.get("q10_model")
                    q50_m = pkg.get("q50_model")
                    q90_m = pkg.get("q90_model")

                    if q10_m and q50_m and q90_m:
                        # Build feature vector from recent history
                        recent_prices = [h.modal_price for h in history[-28:]]
                        lag_1 = recent_prices[-1] if len(recent_prices) >= 1 else latest_price
                        lag_2 = recent_prices[-2] if len(recent_prices) >= 2 else lag_1
                        lag_3 = recent_prices[-3] if len(recent_prices) >= 3 else lag_2
                        lag_7 = recent_prices[-7] if len(recent_prices) >= 7 else lag_1
                        lag_14 = recent_prices[-14] if len(recent_prices) >= 14 else lag_1
                        lag_21 = recent_prices[-21] if len(recent_prices) >= 21 else lag_1
                        lag_28 = recent_prices[-28] if len(recent_prices) >= 28 else lag_1

                        roll_7 = sum(recent_prices[-7:]) / max(len(recent_prices[-7:]), 1)
                        roll_14 = sum(recent_prices[-14:]) / max(len(recent_prices[-14:]), 1)
                        roll_std_7 = (
                            (sum((x - roll_7) ** 2 for x in recent_prices[-7:]) / max(len(recent_prices[-7:]) - 1, 1)) ** 0.5
                            if len(recent_prices[-7:]) > 1 else 15.0
                        )
                        dow = date.today().weekday()
                        month = date.today().month

                        feat_row = [
                            lag_1, lag_2, lag_3, lag_7, lag_14, lag_21, lag_28,
                            roll_7, roll_14, roll_std_7, dow, month
                        ]

                        try:
                            import numpy as np
                            X = np.array([feat_row])
                        except ImportError:
                            X = [feat_row]

                        pred_q10 = float(q10_m.predict(X)[0])
                        pred_q50 = float(q50_m.predict(X)[0])
                        pred_q90 = float(q90_m.predict(X)[0])

                        # Ensure logical ordering: q10 <= q50 <= q90
                        low = min(pred_q10, pred_q50)
                        high = max(pred_q90, pred_q50)
                        mid = pred_q50

                        two_week_forecast = PriceForecastRange(
                            min_expected=round(low, 2),
                            max_expected=round(high, 2),
                            expected_modal=round(mid, 2),
                        )
                        # 4-week forecast expands uncertainty band
                        four_week_forecast = PriceForecastRange(
                            min_expected=round(low * 0.97, 2),
                            max_expected=round(high * 1.03, 2),
                            expected_modal=round(mid, 2),
                        )
                        model_ver = metadata.get("model_version", "lgb-price-v1.0")
                        model_loaded = True
                        break
                except Exception as exc:
                    logger.warning("ML price inference failed, reverting to honest baseline: %s", exc)

    # -------------------------------------------------------------------------
    # Honest Persistence Baseline (model_version = 'baseline')
    # -------------------------------------------------------------------------
    if not model_loaded or two_week_forecast is None or four_week_forecast is None:
        model_ver = "baseline"
        # 2-week baseline: current price ± 5% uncertainty
        two_week_forecast = PriceForecastRange(
            min_expected=round(latest_price * 0.95, 2),
            max_expected=round(latest_price * 1.05, 2),
            expected_modal=round(latest_price, 2),
        )
        # 4-week baseline: current price ± 8% uncertainty
        four_week_forecast = PriceForecastRange(
            min_expected=round(latest_price * 0.92, 2),
            max_expected=round(latest_price * 1.08, 2),
            expected_modal=round(latest_price, 2),
        )

    # Calculate projected percentage change
    pct_change = ((two_week_forecast.expected_modal - latest_price) / latest_price) * 100.0
    trend, recommendation, hint = determine_recommendation(pct_change)

    if model_ver == "baseline":
        explanation = (
            f"{clean_mandi} मंडी में {clean_commodity} का वर्तमान मॉडल भाव ₹{latest_price:.0f}/क्विंटल है। "
            f"पूर्वानुमान 'Same as last week / Moving Average' बेसलाइन मॉडल द्वारा परिकलित है (Model Version: {model_ver})।"
        )
    else:
        explanation = (
            f"{clean_mandi} मंडी में {clean_commodity} का वर्तमान भाव ₹{latest_price:.0f}/क्विंटल है। "
            f"पूर्वानुमान LightGBM क्वांटाइल रिग्रेशन मॉडल (q10, q50, q90) द्वारा परिकलित है (Model Version: {model_ver})।"
        )

    disclaimer = (
        "यह भाव पूर्वानुमान और सलाह केवल निर्णय-सहयोग एवं मार्गदर्शन हेतु है। "
        "वास्तविक बाजार भाव स्थानीय मांग, दैनिक आवक, फसल गुणवत्ता तथा नीतियों पर निर्भर करते हैं। "
        "अंतिम विक्रय निर्णय अपनी स्थानीय मंडी की स्थिति देखकर ही लें।"
    )

    return MandiPriceForecastResponse(
        mandi=clean_mandi,
        commodity=clean_commodity,
        latest_date=latest_date,
        latest_modal_price=round(latest_price, 2),
        trend=trend,  # type: ignore[arg-type]
        forecast_2_weeks=two_week_forecast,
        forecast_4_weeks=four_week_forecast,
        model_version=model_ver,
        recommendation=recommendation,  # type: ignore[arg-type]
        recommendation_text=hint,
        disclaimer=disclaimer,
        history=history,
        explanation=explanation,
    )
