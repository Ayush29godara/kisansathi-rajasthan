#!/usr/bin/env python3
"""
Yield Model Evaluation Pipeline: Leave-One-Year-Out (LOYO) and Leave-One-District-Out (LODO)
Cross-Validation over authentic Rajasthan agricultural production history.

Usage:
    python scripts/evaluate_yield.py --input data/yield_history.csv --crop mustard
"""

import os
import sys
import argparse
import csv
import math
from typing import List, Dict, Any

try:
    import numpy as np
except ImportError:
    np = None


def compute_metrics(y_true: List[float], y_pred: List[float]) -> Dict[str, float]:
    """Compute Root Mean Squared Error (RMSE) and Mean Absolute Error (MAE)."""
    if not y_true:
        return {"mae": 0.0, "rmse": 0.0}
    n = len(y_true)
    mae = sum(abs(t - p) for t, p in zip(y_true, y_pred)) / n
    rmse = math.sqrt(sum((t - p) ** 2 for t, p in zip(y_true, y_pred)) / n)
    return {"mae": round(mae, 2), "rmse": round(rmse, 2)}


def run_loyo_evaluation(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Leave-One-Year-Out cross-validation."""
    years = sorted(list(set(int(r["year"]) for r in records)))
    if len(years) < 2:
        return {"error": "Need at least 2 distinct years in dataset for LOYO."}

    baseline_true, baseline_pred = [], []
    for test_year in years:
        train = [r for r in records if int(r["year"]) != test_year]
        test = [r for r in records if int(r["year"]) == test_year]

        # Calculate district historical means from train fold
        district_means: Dict[str, List[float]] = {}
        for r in train:
            district_means.setdefault(r["district"], []).append(float(r["yield_kg_ha"]))

        overall_mean = sum(float(r["yield_kg_ha"]) for r in train) / len(train)

        for r in test:
            y_actual = float(r["yield_kg_ha"])
            d_vals = district_means.get(r["district"])
            d_mean = (sum(d_vals) / len(d_vals)) if d_vals else overall_mean
            baseline_true.append(y_actual)
            baseline_pred.append(float(d_mean))

    return compute_metrics(baseline_true, baseline_pred)


def run_lodo_evaluation(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Leave-One-District-Out cross-validation."""
    districts = sorted(list(set(r["district"] for r in records)))
    if len(districts) < 2:
        return {"error": "Need at least 2 distinct districts in dataset for LODO."}

    baseline_true, baseline_pred = [], []
    for test_district in districts:
        train = [r for r in records if r["district"] != test_district]
        test = [r for r in records if r["district"] == test_district]

        state_mean = sum(float(r["yield_kg_ha"]) for r in train) / len(train)

        for r in test:
            baseline_true.append(float(r["yield_kg_ha"]))
            baseline_pred.append(state_mean)

    return compute_metrics(baseline_true, baseline_pred)


def main():
    parser = argparse.ArgumentParser(description="Evaluate Yield Models on Real History")
    parser.add_argument("--input", type=str, default="data/yield_history.csv", help="Path to yield CSV file")
    parser.add_argument("--crop", type=str, default="mustard", help="Target crop to evaluate")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[!] Evaluation aborted: Real dataset '{args.input}' not found.")
        print("[*] Per project honesty guidelines, synthetic metrics are never fabricated.")
        print(f"[*] Please supply '{args.input}' containing columns:")
        print("    district,crop,season,year,area_ha,production,yield_kg_ha")
        print("    See scripts/README.md for details.")
        sys.exit(1)

    records = []
    with open(args.input, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("crop", "").lower() == args.crop.lower():
                records.append(row)

    if not records:
        print(f"[!] No records found for crop '{args.crop}' in '{args.input}'.")
        sys.exit(1)

    print(f"[*] Running Honest Evaluation for Crop: {args.crop.upper()} ({len(records)} records)")
    loyo_metrics = run_loyo_evaluation(records)
    print(f" -> LOYO (Leave-One-Year-Out) Baseline:     MAE={loyo_metrics.get('mae')} kg/ha, RMSE={loyo_metrics.get('rmse')} kg/ha")

    lodo_metrics = run_lodo_evaluation(records)
    print(f" -> LODO (Leave-One-District-Out) Baseline: MAE={lodo_metrics.get('mae')} kg/ha, RMSE={lodo_metrics.get('rmse')} kg/ha")


if __name__ == "__main__":
    main()
