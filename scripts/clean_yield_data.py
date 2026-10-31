#!/usr/bin/env python3
"""
District-Level Agricultural Yield Data Cleaning & Boundary Normalization.

Maps newly carved administrative districts to the fixed 33-district historical
statistical standard (1997-2023 DES benchmark), normalizes crop and season names,
computes yield if missing, and filters statistical outliers.

Usage:
    python scripts/clean_yield_data.py --input data/yield_data/raw_yield.csv --output data/yield_data/cleaned_yield.csv
    python scripts/clean_yield_data.py --synthetic --output data/yield_data/cleaned_yield.csv
"""

import os
import sys
import csv
import random
import argparse
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("clean_yield_data")

# ---------------------------------------------------------------------------
# 33 Historical Statistical Districts of Rajasthan
# ---------------------------------------------------------------------------
HISTORICAL_33_DISTRICTS = {
    "Ajmer", "Alwar", "Banswara", "Baran", "Barmer", "Bharatpur", "Bhilwara",
    "Bikaner", "Bundi", "Chittorgarh", "Churu", "Dausa", "Dholpur", "Dungarpur",
    "Hanumangarh", "Jaipur", "Jaisalmer", "Jalore", "Jhalawar", "Jhunjhunu",
    "Jodhpur", "Karauli", "Kota", "Nagaur", "Pali", "Pratapgarh", "Rajsamand",
    "Sawai Madhopur", "Sikar", "Sirohi", "Sri Ganganagar", "Tonk", "Udaipur"
}

# ---------------------------------------------------------------------------
# District Name Standardization & Boundary Mapping to 33-district standard
# ---------------------------------------------------------------------------
DISTRICT_SYNONYMS_AND_MAPPING: Dict[str, str] = {
    # Newly created administrative districts mapped to historical parent
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

    # Spelling and transliteration variations
    "chittaurgarh": "Chittorgarh",
    "chittore": "Chittorgarh",
    "ganganagar": "Sri Ganganagar",
    "shri ganganagar": "Sri Ganganagar",
    "dhaulpur": "Dholpur",
    "jalore": "Jalore",
    "jalor": "Jalore",
    "jhunjhunun": "Jhunjhunu",
    "s-madhopur": "Sawai Madhopur",
    "sawai madhopur": "Sawai Madhopur",
}

# ---------------------------------------------------------------------------
# Crop & Season Normalization
# ---------------------------------------------------------------------------
CROP_MAPPING: Dict[str, str] = {
    "mustard": "Mustard",
    "rapeseed & mustard": "Mustard",
    "rapeseed and mustard": "Mustard",
    "sarson": "Mustard",
    "bajra": "Bajra",
    "pearl millet": "Bajra",
    "wheat": "Wheat",
    "gehun": "Wheat",
    "soybean": "Soybean",
    "soya bean": "Soybean",
    "guar": "Guar",
    "cluster bean": "Guar",
    "gram": "Gram",
    "chana": "Gram",
    "chickpea": "Gram",
}

SEASON_MAPPING: Dict[str, str] = {
    "kharif": "Kharif",
    "rabi": "Rabi",
    "whole year": "Whole Year",
    "annual": "Whole Year",
    "summer": "Summer",
}

# Biological realistic yield bounds (kg/ha) for anomaly detection in Rajasthan
YIELD_BOUNDS: Dict[str, tuple[float, float]] = {
    "Mustard": (200.0, 3500.0),
    "Bajra": (100.0, 4000.0),
    "Wheat": (500.0, 6500.0),
    "Soybean": (200.0, 3000.0),
    "Guar": (50.0, 1800.0),
    "Gram": (150.0, 2800.0),
}


def normalize_district(raw_name: str) -> Optional[str]:
    """Map raw district name to standard 33 historical district boundary."""
    clean = raw_name.strip()
    if clean in HISTORICAL_33_DISTRICTS:
        return clean
    lower = clean.lower()
    if lower in DISTRICT_SYNONYMS_AND_MAPPING:
        return DISTRICT_SYNONYMS_AND_MAPPING[lower]
    # Check partial match
    for syn, target in DISTRICT_SYNONYMS_AND_MAPPING.items():
        if syn in lower or lower in syn:
            return target
    for target in HISTORICAL_33_DISTRICTS:
        if target.lower() in lower:
            return target
    return None


def normalize_crop(raw_crop: str) -> Optional[str]:
    """Normalize crop name to standard capitalized representation."""
    lower = raw_crop.strip().lower()
    return CROP_MAPPING.get(lower)


def normalize_season(raw_season: str) -> str:
    """Normalize crop season."""
    lower = raw_season.strip().lower()
    return SEASON_MAPPING.get(lower, "Whole Year")


def clean_yield_file(input_path: str, output_path: str) -> None:
    """Read raw yield CSV, standardize boundaries and values, write clean CSV."""
    if not os.path.exists(input_path):
        logger.error("Raw yield file not found: %s", input_path)
        sys.exit(1)

    logger.info("Cleaning raw yield file: %s", input_path)
    clean_rows: List[Dict[str, Any]] = []
    skipped_count = 0

    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Check state if present
            state = row.get("State", "Rajasthan").strip()
            if state and "rajasthan" not in state.lower():
                skipped_count += 1
                continue

            # District mapping
            raw_district = row.get("District", "")
            district = normalize_district(raw_district)
            if not district:
                skipped_count += 1
                continue

            # Crop mapping
            raw_crop = row.get("Crop", "")
            crop = normalize_crop(raw_crop)
            if not crop:
                skipped_count += 1
                continue

            # Season
            season = normalize_season(row.get("Season", "Kharif"))

            # Year
            try:
                year_val = str(row.get("Year", "")).strip()
                # Handle "2021-22" or "2021"
                year = int(year_val.split("-")[0].split("/")[0])
            except (ValueError, IndexError):
                skipped_count += 1
                continue

            # Area & Production
            try:
                area_ha = float(row.get("Area_Hectares", row.get("Area", 0)))
                production_tonnes = float(row.get("Production_Tonnes", row.get("Production", 0)))
            except (ValueError, TypeError):
                skipped_count += 1
                continue

            if area_ha <= 0:
                skipped_count += 1
                continue

            # Compute yield (kg/ha)
            raw_yield = row.get("Yield_Kg_Per_Hectare", row.get("Yield", None))
            try:
                if raw_yield is not None and str(raw_yield).strip() != "":
                    yield_val = float(raw_yield)
                else:
                    yield_val = (production_tonnes * 1000.0) / area_ha
            except (ValueError, TypeError):
                yield_val = (production_tonnes * 1000.0) / area_ha

            # Outlier filter
            bounds = YIELD_BOUNDS.get(crop, (50.0, 8000.0))
            if yield_val < bounds[0] or yield_val > bounds[1]:
                skipped_count += 1
                continue

            clean_rows.append({
                "district": district,
                "crop": crop,
                "season": season,
                "year": year,
                "area_ha": round(area_ha, 2),
                "production_tonnes": round(production_tonnes, 2),
                "yield_kg_ha": round(yield_val, 2),
            })

    # Sort deterministically
    clean_rows.sort(key=lambda r: (r["crop"], r["district"], r["year"]))

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    fieldnames = ["district", "crop", "season", "year", "area_ha", "production_tonnes", "yield_kg_ha"]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clean_rows)

    logger.info("Cleaning complete. Retained: %d rows (Skipped/Filtered: %d)", len(clean_rows), skipped_count)
    logger.info("Saved standardized yield data to: %s", output_path)


def generate_synthetic_dataset(output_path: str) -> None:
    """Generate realistic synthetic yield dataset for testing & pipeline calibration."""
    logger.info("Generating realistic synthetic multi-year yield dataset for 33 Rajasthan districts...")
    random.seed(42)

    crop_configs = {
        "Mustard": {"season": "Rabi", "mean_yield": 1500, "std": 250, "area_range": (30000, 350000)},
        "Bajra": {"season": "Kharif", "mean_yield": 1100, "std": 350, "area_range": (50000, 450000)},
        "Wheat": {"season": "Rabi", "mean_yield": 3400, "std": 450, "area_range": (40000, 300000)},
        "Soybean": {"season": "Kharif", "mean_yield": 1200, "std": 220, "area_range": (15000, 200000)},
        "Guar": {"season": "Kharif", "mean_yield": 420, "std": 110, "area_range": (20000, 300000)},
    }

    years = list(range(2005, 2024))
    rows: List[Dict[str, Any]] = []

    for district in sorted(HISTORICAL_33_DISTRICTS):
        # District climatic modifier (e.g. western arid vs south-eastern irrigated)
        if district in {"Bikaner", "Jodhpur", "Jaisalmer", "Barmer", "Churu"}:
            mod = 0.75
        elif district in {"Sri Ganganagar", "Hanumangarh", "Kota", "Baran", "Bundi"}:
            mod = 1.25
        else:
            mod = 1.0

        for crop, cfg in crop_configs.items():
            # Skip crops not commonly grown in specific regions
            if crop == "Soybean" and mod < 1.0:
                continue

            for year in years:
                # Annual weather variation (e.g. 2009 drought, 2011 good monsoon)
                if year == 2009:
                    yr_factor = 0.65
                elif year in {2011, 2016, 2020}:
                    yr_factor = 1.20
                else:
                    yr_factor = 1.0 + random.uniform(-0.15, 0.15)

                area = random.uniform(*cfg["area_range"])
                base_yield = cfg["mean_yield"] * mod * yr_factor
                actual_yield = max(50.0, random.gauss(base_yield, cfg["std"] * 0.5))
                production = (actual_yield * area) / 1000.0

                rows.append({
                    "district": district,
                    "crop": crop,
                    "season": cfg["season"],
                    "year": year,
                    "area_ha": round(area, 2),
                    "production_tonnes": round(production, 2),
                    "yield_kg_ha": round(actual_yield, 2),
                })

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    fieldnames = ["district", "crop", "season", "year", "area_ha", "production_tonnes", "yield_kg_ha"]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info("Successfully generated %d yield records across 2005-2023 -> %s", len(rows), output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="KisanSathi Yield Data Cleaning Script")
    parser.add_argument("--input", type=str, default="data/yield_data/raw_yield.csv", help="Input raw CSV path")
    parser.add_argument("--output", type=str, default="data/yield_data/cleaned_yield.csv", help="Output cleaned CSV path")
    parser.add_argument("--synthetic", action="store_true", help="Generate realistic synthetic historical dataset")
    args = parser.parse_args()

    if args.synthetic:
        generate_synthetic_dataset(args.output)
    else:
        clean_yield_file(args.input, args.output)


if __name__ == "__main__":
    main()
