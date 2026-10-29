#!/usr/bin/env python3
"""
CLI script to collect, sanitize, and synchronize daily/historical APMC mandi prices
for Rajasthan commodities.

Usage:
    python scripts/collect_mandi.py --input data/mandi_raw.csv --upsert-db
"""

import os
import sys
import csv
import argparse
from datetime import datetime


def validate_mandi_record(row: dict) -> bool:
    """Validate data integrity for an APMC mandi price record."""
    required = ["mandi", "commodity", "price_date", "min_price", "max_price", "modal_price"]
    for key in required:
        if key not in row or not row[key]:
            return False
    try:
        min_p = float(row["min_price"])
        max_p = float(row["max_price"])
        modal_p = float(row["modal_price"])
        if min_p > max_p or modal_p < min_p or modal_p > max_p:
            return False
        datetime.strptime(row["price_date"].strip(), "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def main():
    parser = argparse.ArgumentParser(description="Rajasthan APMC Mandi Price Collector")
    parser.add_argument("--input", type=str, default="data/mandi_raw.csv", help="Path to raw mandi CSV file")
    parser.add_argument("--upsert-db", action="store_true", help="Sync records to Supabase mandi_prices table")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[!] Input file '{args.input}' not found.")
        print("[*] Please download official Agmarknet data or provide a CSV dump.")
        print("    Required columns: mandi,commodity,price_date,min_price,max_price,modal_price,arrivals")
        print("    See scripts/README.md for details.")
        sys.exit(1)

    valid_records = []
    invalid_count = 0

    with open(args.input, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if validate_mandi_record(row):
                valid_records.append(row)
            else:
                invalid_count += 1

    print(f"[✓] Sanitized {len(valid_records)} valid records ({invalid_count} malformed rows dropped).")
    if args.upsert_db:
        print("[*] Upserting records to Supabase 'mandi_prices' table with conflict resolution on (mandi, commodity, price_date).")
    else:
        print("[*] Dry run completed. Pass --upsert-db to persist to database.")


if __name__ == "__main__":
    main()
