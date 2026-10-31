#!/usr/bin/env python3
"""
Organize raw downloaded disease datasets into standardized class folders under data/disease_data/raw/.

Handles:
1. Pearl millet dataset (reads _classes.csv from train/test/valid, extracts bajra_rust, bajra_downy_mildew, bajra_healthy).
2. Mustard disease dataset (reads _annotations.coco.json from train/test/valid, extracts mustard_blight, mustard_leaf_miner, mustard_armyworm).
3. Normalizes wheat and tomato folder names in data/disease_data/raw/ to clean snake_case.
"""

import os
import shutil
import csv
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("organize_datasets")

RAW_DIR = "data/disease_data/raw"
MILLET_DIR = "data/disease_data/pearl millet dataset"
MUSTARD_DIR = "data/disease_data/mustard disease.v5i.coco"


def organize_pearl_millet():
    """Extract and sort pearl millet images into bajra class folders."""
    if not os.path.exists(MILLET_DIR):
        logger.warning("Pearl millet dataset directory not found: %s", MILLET_DIR)
        return

    logger.info("Organizing Pearl Millet dataset...")
    count = 0

    for split in ["train", "test", "valid"]:
        split_dir = os.path.join(MILLET_DIR, split)
        csv_file = os.path.join(split_dir, "_classes.csv")
        if not os.path.exists(csv_file):
            continue

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fname = row.get("filename", "").strip()
                if not fname:
                    continue

                clean_row = {k.strip(): v.strip() for k, v in row.items() if k}
                category = None
                if clean_row.get("Downy") == "1":
                    category = "bajra_downy_mildew"
                elif clean_row.get("Rust") == "1":
                    category = "bajra_rust"
                elif clean_row.get("Healthy") == "1":
                    category = "bajra_healthy"

                if not category:
                    continue

                src_path = os.path.join(split_dir, fname)
                if not os.path.exists(src_path):
                    continue

                dest_dir = os.path.join(RAW_DIR, category)
                os.makedirs(dest_dir, exist_ok=True)
                dest_path = os.path.join(dest_dir, f"{split}_{fname}")

                if not os.path.exists(dest_path):
                    shutil.copy2(src_path, dest_path)
                    count += 1

    logger.info("Successfully organized %d Pearl Millet images into %s", count, RAW_DIR)


def organize_mustard():
    """Extract and sort mustard images into mustard class folders."""
    if not os.path.exists(MUSTARD_DIR):
        logger.warning("Mustard dataset directory not found: %s", MUSTARD_DIR)
        return

    logger.info("Organizing Mustard dataset...")
    cat_map = {1: "mustard_blight", 2: "mustard_leaf_miner", 3: "mustard_armyworm"}
    count = 0

    for split in ["train", "test", "valid"]:
        split_dir = os.path.join(MUSTARD_DIR, split)
        ann_file = os.path.join(split_dir, "_annotations.coco.json")
        if not os.path.exists(ann_file):
            continue

        with open(ann_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        img_id_to_file = {img["id"]: img["file_name"] for img in data.get("images", [])}
        img_to_cat = {}
        for ann in data.get("annotations", []):
            cid = ann.get("category_id")
            if cid in cat_map:
                img_to_cat[ann["image_id"]] = cat_map[cid]

        for img_id, category in img_to_cat.items():
            fname = img_id_to_file.get(img_id)
            if not fname:
                continue

            src_path = os.path.join(split_dir, fname)
            if not os.path.exists(src_path):
                continue

            dest_dir = os.path.join(RAW_DIR, category)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, f"{split}_{fname}")

            if not os.path.exists(dest_path):
                shutil.copy2(src_path, dest_path)
                count += 1

    logger.info("Successfully organized %d Mustard images into %s", count, RAW_DIR)


def normalize_raw_subfolders():
    """Normalize raw class folder names to clean lowercase snake_case (APFS case-insensitive safe)."""
    if not os.path.exists(RAW_DIR):
        return

    folder_map = {
        "wheat Brown rust": "wheat_brown_rust",
        "wheat Healthy": "wheat_healthy",
        "wheat Loose Smut": "wheat_loose_smut",
        "wheat Septoria": "wheat_septoria",
        "wheatYellow rust": "wheat_yellow_rust",
        "Tomato_Bacterial_spot": "tomato_bacterial_spot",
        "Tomato_Early_blight": "tomato_early_blight",
        "Tomato_Late_blight": "tomato_late_blight",
        "Tomato_Leaf_Mold": "tomato_leaf_mold",
        "Tomato_Septoria_leaf_spot": "tomato_septoria_leaf_spot",
        "Tomato_Spider_mites_Two_spotted_spider_mite": "tomato_spider_mites",
        "Tomato__Target_Spot": "tomato_target_spot",
        "Tomato__Tomato_YellowLeaf__Curl_Virus": "tomato_yellow_leaf_curl",
        "Tomato__Tomato_mosaic_virus": "tomato_mosaic_virus",
        "Tomato_healthy": "tomato_healthy",
    }

    for old_name, new_name in folder_map.items():
        old_path = os.path.join(RAW_DIR, old_name)
        new_path = os.path.join(RAW_DIR, new_name)
        if os.path.exists(old_path) and old_name != new_name:
            tmp_path = os.path.join(RAW_DIR, f"__tmp_{new_name}__")
            try:
                os.rename(old_path, tmp_path)
                os.rename(tmp_path, new_path)
                logger.info("Normalized folder: '%s' -> '%s'", old_name, new_name)
            except Exception as e:
                logger.warning("Could not rename %s to %s: %s", old_name, new_name, e)


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    normalize_raw_subfolders()
    organize_pearl_millet()
    organize_mustard()
    logger.info("All disease datasets organized in %s successfully!", RAW_DIR)


if __name__ == "__main__":
    main()
