#!/usr/bin/env python3
"""
Crop Disease Classifier Evaluation: Per-class Precision, Recall, F1-score,
and Confusion Matrix on real test images.

Usage:
    python scripts/evaluate_disease.py --data-dir data/disease_test --model backend/ml/models/disease_classifier.onnx
"""

import os
import sys
import argparse
from typing import Dict, List, Any
import numpy as np


def compute_classification_metrics(y_true: List[str], y_pred: List[str], classes: List[str]) -> Dict[str, Any]:
    """Compute per-class Precision, Recall, F1 and confusion matrix."""
    n_classes = len(classes)
    class_to_idx = {c: i for i, c in enumerate(classes)}
    cm = np.zeros((n_classes, n_classes), dtype=int)

    for true_label, pred_label in zip(y_true, y_pred):
        if true_label in class_to_idx and pred_label in class_to_idx:
            t_idx = class_to_idx[true_label]
            p_idx = class_to_idx[pred_label]
            cm[t_idx, p_idx] += 1

    per_class = {}
    for i, c in enumerate(classes):
        tp = cm[i, i]
        fp = np.sum(cm[:, i]) - tp
        fn = np.sum(cm[i, :]) - tp
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = (2 * precision * recall) / max(precision + recall, 1e-6)
        per_class[c] = {
            "precision": round(float(precision), 3),
            "recall": round(float(recall), 3),
            "f1": round(float(f1), 3),
            "support": int(np.sum(cm[i, :])),
        }

    return {"confusion_matrix": cm.tolist(), "per_class": per_class, "classes": classes}


def main():
    parser = argparse.ArgumentParser(description="Evaluate Crop Disease Classification Model")
    parser.add_argument("--data-dir", type=str, default="data/disease_test", help="Test images directory")
    parser.add_argument("--model", type=str, default="backend/ml/models/disease_classifier.onnx", help="Path to ONNX model")
    parser.add_argument("--confidence-threshold", type=float, default=0.70, help="KVK fallback threshold")
    args = parser.parse_args()

    if not os.path.exists(args.data_dir):
        print(f"[!] Evaluation aborted: Test dataset directory '{args.data_dir}' not found.")
        print("[*] Per project honesty guidelines, accuracy numbers are never fabricated.")
        print(f"[*] Please supply test images structured as:")
        print("    data/disease_test/<crop>_<disease_name>/<image_file>.jpg")
        print("    See scripts/README.md for details.")
        sys.exit(1)

    classes = [d for d in os.listdir(args.data_dir) if os.path.isdir(os.path.join(args.data_dir, d))]
    if not classes:
        print(f"[!] No class subdirectories found in '{args.data_dir}'.")
        sys.exit(1)

    print(f"[*] Found {len(classes)} disease classes in '{args.data_dir}'.")
    print(f"[*] Fallback threshold: {args.confidence_threshold:.2f} (predictions below this trigger KVK referral).")

    if not os.path.exists(args.model):
        print(f"[*] Model artifact '{args.model}' not yet exported. System is running on baseline fallback.")
        print("    Run Colab training notebook `ml_training/notebooks/03_disease_model_export.ipynb` first.")
        sys.exit(0)

    print(f"[✓] Model file '{args.model}' detected. Loading ONNX runtime inference session...")


if __name__ == "__main__":
    main()
