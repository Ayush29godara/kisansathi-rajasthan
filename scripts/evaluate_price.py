#!/usr/bin/env python3
"""
Mandi Price Forecasting Evaluation Pipeline: Walk-Forward Validation
across 14-day and 28-day forecasting horizons.

Usage:
    python scripts/evaluate_price.py --input data/mandi_data/cleaned_mandi.csv --commodity mustard --mandi Alwar
"""

import os
import sys
import csv
import math
import argparse
from datetime import datetime
from typing import List, Dict, Any

try:
    import numpy as np
except ImportError:
    np = None


def run_walk_forward_evaluation(
    records: List[Dict[str, Any]],
    horizon_days: int = 14,
    min_train_size: int = 14,
) -> Dict[str, Any]:
    """
    Perform walk-forward validation:
    Train window expands, model predicts t + horizon_days, evaluate error.
    Persistence baseline: Pred(t + h) = Price(t).
    """
    sorted_records = sorted(records, key=lambda x: x["price_date"])
    prices = [float(r["modal_price"]) for r in sorted_records]
    n = len(prices)

    if n < min_train_size + horizon_days:
        return {"error": f"Insufficient data points ({n} found, need >= {min_train_size + horizon_days})"}

    y_true = []
    y_pred_baseline = []
    correct_directions = 0
    total_direction_checks = 0

    for t in range(min_train_size, n - horizon_days):
        actual_future_price = prices[t + horizon_days]
        current_price = prices[t]

        # Persistence baseline predicts current price continues
        y_true.append(actual_future_price)
        y_pred_baseline.append(current_price)

        # Direction check: Did price rise or fall compared to previous week?
        prev_price = prices[t - 7] if t >= 7 else current_price
        actual_diff = actual_future_price - current_price
        trend_diff = current_price - prev_price

        if (actual_diff >= 0 and trend_diff >= 0) or (actual_diff < 0 and trend_diff < 0):
            correct_directions += 1
        total_direction_checks += 1

    if np is not None:
        y_t = np.array(y_true)
        y_p = np.array(y_pred_baseline)
        mae = float(np.mean(np.abs(y_t - y_p)))
        rmse = float(np.sqrt(np.mean((y_t - y_p) ** 2)))
    else:
        abs_diffs = [abs(yt - yp) for yt, yp in zip(y_true, y_pred_baseline)]
        sq_diffs = [(yt - yp) ** 2 for yt, yp in zip(y_true, y_pred_baseline)]
        mae = sum(abs_diffs) / max(len(abs_diffs), 1)
        rmse = math.sqrt(sum(sq_diffs) / max(len(sq_diffs), 1))

    dir_acc = float((correct_directions / max(total_direction_checks, 1)) * 100.0)

    return {
        "horizon_days": horizon_days,
        "eval_windows": len(y_true),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "directional_accuracy_pct": round(dir_acc, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Walk-Forward Mandi Price Evaluation")
    parser.add_argument("--input", type=str, default="data/mandi_data/cleaned_mandi.csv", help="Historical price CSV")
    parser.add_argument("--commodity", type=str, default="mustard", help="Target commodity")
    parser.add_argument("--mandi", type=str, default="Alwar", help="Target mandi")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[!] Evaluation aborted: Historical dataset '{args.input}' not found.")
        print("[*] Per project honesty guidelines, synthetic metrics are never fabricated.")
        print(f"[*] Please supply '{args.input}' containing columns:")
        print("    mandi,commodity,price_date,modal_price")
        print("    See scripts/README.md for details.")
        sys.exit(1)

    records = []
    with open(args.input, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("commodity", "").lower() == args.commodity.lower() and
                    row.get("mandi", "").lower() == args.mandi.lower()):
                records.append(row)

    if not records:
        print(f"[!] No matching records for {args.commodity} in {args.mandi}.")
        sys.exit(1)

    print(f"[*] Running Walk-Forward Evaluation for {args.commodity.upper()} at {args.mandi} ({len(records)} days)")
    res_14 = run_walk_forward_evaluation(records, horizon_days=14)
    if "error" in res_14:
        print(f" -> 14-Day Horizon: {res_14['error']}")
    else:
        print(f" -> 14-Day Horizon Baseline: MAE=₹{res_14.get('mae')}, RMSE=₹{res_14.get('rmse')}, Direction Acc={res_14.get('directional_accuracy_pct')}%")

    res_28 = run_walk_forward_evaluation(records, horizon_days=28)
    if "error" in res_28:
        print(f" -> 28-Day Horizon: {res_28['error']}")
    else:
        print(f" -> 28-Day Horizon Baseline: MAE=₹{res_28.get('mae')}, RMSE=₹{res_28.get('rmse')}, Direction Acc={res_28.get('directional_accuracy_pct')}%")


if __name__ == "__main__":
    main()
