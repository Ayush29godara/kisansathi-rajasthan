"""Train and export MobileNetV3-Small (24-class) crop disease classifier to ONNX.

Uses Apple Silicon MPS acceleration when available, balanced class sampling to
handle class imbalance, evaluates on val and test splits, and exports a single
self-contained ONNX file for both frontend (onnxruntime-web) and backend inference.
"""

import json
import os
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import onnx
import onnxruntime as ort
from PIL import Image
from sklearn.metrics import accuracy_score, f1_score
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

ROOT_DIR = Path(__file__).resolve().parent.parent
torch.hub.set_dir(str(ROOT_DIR / "ml_training" / ".torch_cache"))
SPLITS_DIR = ROOT_DIR / "data" / "disease_data" / "splits"
FRONTEND_MODELS_DIR = ROOT_DIR / "frontend" / "public" / "models"
BACKEND_MODELS_DIR = ROOT_DIR / "backend" / "ml" / "models"

FOLDER_TO_LABEL: Dict[str, str] = {
    "bajra_blast": "bajra_blast",
    "bajra_downy_mildew": "bajra_downy_mildew",
    "bajra_healthy": "bajra_healthy",
    "bajra_rust": "bajra_rust",
    "mustard_armyworm": "mustard_armyworm",
    "mustard_blight": "mustard_alternaria_blight",
    "mustard_healthy": "mustard_healthy",
    "mustard_leaf_miner": "mustard_leaf_miner",
    "mustard_white_rust": "mustard_white_rust",
    "tomato_bacterial_spot": "tomato_bacterial_spot",
    "tomato_early_blight": "tomato_early_blight",
    "tomato_healthy": "tomato_healthy",
    "tomato_late_blight": "tomato_late_blight",
    "tomato_leaf_mold": "tomato_leaf_mold",
    "tomato_mosaic_virus": "tomato_mosaic_virus",
    "tomato_septoria_leaf_spot": "tomato_septoria_leaf_spot",
    "tomato_spider_mites": "tomato_spider_mites",
    "tomato_target_spot": "tomato_target_spot",
    "tomato_yellow_leaf_curl": "tomato_yellow_leaf_curl",
    "wheat_brown_rust": "wheat_brown_rust",
    "wheat_healthy": "wheat_healthy",
    "wheat_loose_smut": "wheat_loose_smut",
    "wheat_septoria": "wheat_septoria",
    "wheat_yellow_rust": "wheat_yellow_rust",
}

HINDI_LABELS: Dict[str, str] = {
    "bajra_blast": "बाजरा पत्ती धब्बा / ब्लास्ट (Bajra Blast)",
    "bajra_downy_mildew": "बाजरा हरित बाली / जोगिया (Downy Mildew)",
    "bajra_healthy": "बाजरा स्वस्थ पत्ती (Healthy Bajra)",
    "bajra_rust": "बाजरा रतुआ रोग (Bajra Rust)",
    "mustard_armyworm": "सरसों सैनिक कीट / सूंडी (Armyworm)",
    "mustard_alternaria_blight": "सरसों झुलसा रोग (Alternaria Blight)",
    "mustard_healthy": "सरसों स्वस्थ पत्ती (Healthy Mustard)",
    "mustard_leaf_miner": "सरसों पत्ती सुरंगक (Leaf Miner)",
    "mustard_white_rust": "सरसों सफेद रोली (White Rust)",
    "tomato_bacterial_spot": "टमाटर जीवाणु धब्बा रोग (Bacterial Spot)",
    "tomato_early_blight": "टमाटर अगेती झुलसा (Early Blight)",
    "tomato_healthy": "टमाटर स्वस्थ पत्ती (Healthy Tomato)",
    "tomato_late_blight": "टमाटर पछेती झुलसा (Late Blight)",
    "tomato_leaf_mold": "टमाटर पत्ती फफूंद (Leaf Mold)",
    "tomato_mosaic_virus": "टमाटर मोजेक वायरस (Mosaic Virus)",
    "tomato_septoria_leaf_spot": "टमाटर सेप्टोरिया पत्ती धब्बा (Septoria Leaf Spot)",
    "tomato_spider_mites": "टमाटर लाल मकड़ी / माइट्स (Spider Mites)",
    "tomato_target_spot": "टमाटर टारगेट स्पॉट (Target Spot)",
    "tomato_yellow_leaf_curl": "टमाटर पर्ण कुंचन वायरस / माथा बंधना (Yellow Leaf Curl)",
    "wheat_brown_rust": "गेहूं भूरा रतुआ (Brown Rust)",
    "wheat_healthy": "गेहूं स्वस्थ पत्ती (Healthy Wheat)",
    "wheat_loose_smut": "गेहूं अनावृत कंडवा / कांगियारी (Loose Smut)",
    "wheat_septoria": "गेहूं सेप्टोरिया पर्ण झुलसा (Septoria Leaf Blotch)",
    "wheat_yellow_rust": "गेहूं पीला रतुआ (Yellow Rust)",
}

FOLDERS_SORTED = sorted(FOLDER_TO_LABEL.keys())
CLASSES_SORTED = [FOLDER_TO_LABEL[f] for f in FOLDERS_SORTED]


def collect_split_files(split_dir: Path) -> Dict[int, List[Path]]:
    by_class: Dict[int, List[Path]] = {i: [] for i in range(len(FOLDERS_SORTED))}
    for idx, folder_name in enumerate(FOLDERS_SORTED):
        cdir = split_dir / folder_name
        if not cdir.exists():
            continue
        for p in sorted(cdir.iterdir()):
            if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                by_class[idx].append(p)
    return by_class


class BalancedTrainDataset(Dataset):
    """Samples `samples_per_class` images per class each epoch."""

    def __init__(self, by_class: Dict[int, List[Path]], samples_per_class: int, transform):
        self.by_class = by_class
        self.samples_per_class = samples_per_class
        self.transform = transform
        self.items: List[Tuple[Path, int]] = []
        self.resample()

    def resample(self) -> None:
        self.items = []
        for cls_idx, paths in self.by_class.items():
            if not paths:
                continue
            if len(paths) >= self.samples_per_class:
                chosen = random.sample(paths, self.samples_per_class)
            else:
                chosen = [random.choice(paths) for _ in range(self.samples_per_class)]
            for p in chosen:
                self.items.append((p, cls_idx))
        random.shuffle(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int):
        path, label = self.items[index]
        try:
            with Image.open(path) as img:
                img = img.convert("RGB")
                tensor = self.transform(img)
        except Exception:
            tensor = torch.zeros(3, 224, 224)
        return tensor, label


class EvalDataset(Dataset):
    def __init__(self, by_class: Dict[int, List[Path]], transform, max_per_class: int = 0):
        self.items: List[Tuple[Path, int]] = []
        for cls_idx, paths in by_class.items():
            subset = paths[:max_per_class] if max_per_class > 0 else paths
            for p in subset:
                self.items.append((p, cls_idx))
        self.transform = transform

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int):
        path, label = self.items[index]
        try:
            with Image.open(path) as img:
                img = img.convert("RGB")
                tensor = self.transform(img)
        except Exception:
            tensor = torch.zeros(3, 224, 224)
        return tensor, label


def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> Tuple[float, float]:
    model.eval()
    all_preds: List[int] = []
    all_targets: List[int] = []
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            logits = model(x)
            preds = logits.argmax(dim=1).cpu().tolist()
            all_preds.extend(preds)
            all_targets.extend(y.tolist())
    acc = accuracy_score(all_targets, all_preds)
    f1 = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    return float(acc), float(f1)


def main() -> None:
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using device: {device}")

    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.75, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    train_by_class = collect_split_files(SPLITS_DIR / "train")
    val_by_class = collect_split_files(SPLITS_DIR / "val")
    test_by_class = collect_split_files(SPLITS_DIR / "test")

    train_ds = BalancedTrainDataset(train_by_class, samples_per_class=180, transform=train_transform)
    val_ds = EvalDataset(val_by_class, transform=eval_transform)
    test_ds = EvalDataset(test_by_class, transform=eval_transform)

    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=64, shuffle=False, num_workers=0)

    print(f"Train samples/epoch: {len(train_ds)}, Val: {len(val_ds)}, Test: {len(test_ds)}")

    weights = models.MobileNet_V3_Small_Weights.DEFAULT
    model = models.mobilenet_v3_small(weights=weights)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, len(CLASSES_SORTED))
    model = model.to(device)

    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1.5e-3, weight_decay=1e-4)
    epochs = 6
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_acc = 0.0
    best_state = None

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        train_ds.resample()
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * x.size(0)
            preds = logits.argmax(dim=1)
            correct += (preds == y).sum().item()
            total += x.size(0)

        scheduler.step()
        train_acc = correct / max(total, 1)
        val_acc, val_f1 = evaluate(model, val_loader, device)
        dt = time.time() - t0
        print(
            f"Epoch {epoch}/{epochs} ({dt:.1f}s) | "
            f"Train Loss: {running_loss / max(total, 1):.4f} Acc: {train_acc:.4f} | "
            f"Val Acc: {val_acc:.4f} Macro-F1: {val_f1:.4f}"
        )

        if val_acc >= best_val_acc:
            best_val_acc = val_acc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)

    test_acc, test_f1 = evaluate(model, test_loader, device)
    print(f"Final Test Top-1 Accuracy: {test_acc:.4f} | Test Macro-F1: {test_f1:.4f}")

    # Export to ONNX (single self-contained file)
    model_cpu = model.cpu().eval()
    dummy_input = torch.randn(1, 3, 224, 224)

    FRONTEND_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    BACKEND_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    tmp_onnx = BACKEND_MODELS_DIR / "crop_disease_raw.onnx"
    final_backend_onnx = BACKEND_MODELS_DIR / "crop_disease.onnx"
    final_frontend_onnx = FRONTEND_MODELS_DIR / "crop_disease.onnx"

    try:
        torch.onnx.export(
            model_cpu,
            dummy_input,
            str(tmp_onnx),
            input_names=["input"],
            output_names=["output"],
            opset_version=13,
            do_constant_folding=True,
            dynamo=False,
        )
    except TypeError:
        torch.onnx.export(
            model_cpu,
            dummy_input,
            str(tmp_onnx),
            input_names=["input"],
            output_names=["output"],
            opset_version=13,
            do_constant_folding=True,
        )

    # Ensure single file without external .data
    onnx_model = onnx.load(str(tmp_onnx), load_external_data=True)
    onnx.save_model(onnx_model, str(final_backend_onnx), save_as_external_data=False)
    onnx.save_model(onnx_model, str(final_frontend_onnx), save_as_external_data=False)
    if tmp_onnx.exists():
        tmp_onnx.unlink()
    data_sidecar = BACKEND_MODELS_DIR / "crop_disease_raw.onnx.data"
    if data_sidecar.exists():
        data_sidecar.unlink()

    # Verify with ONNXRuntime
    sess = ort.InferenceSession(str(final_backend_onnx), providers=["CPUExecutionProvider"])
    out = sess.run(None, {"input": dummy_input.numpy()})
    print("ONNX output shape:", out[0].shape, "File size MB:", round(final_backend_onnx.stat().st_size / (1024 * 1024), 2))

    # Save updated crop_disease_labels.json
    labels_payload = {
        "model_name": "MobileNetV3-Small Crop Disease Classifier (Rajasthan 24-Class)",
        "model_version": "mobilenet-v3-small-v2.1",
        "val_top1_accuracy": round(best_val_acc, 4),
        "test_top1_accuracy": round(test_acc, 4),
        "test_macro_f1": round(test_f1, 4),
        "classes": CLASSES_SORTED,
        "class_labels_hi": HINDI_LABELS,
        "input_size": [1, 3, 224, 224],
        "normalization": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225],
        },
        "confidence_threshold": 0.70,
        "fallback_policy": "Show not sure notice and prompt KVK referral whenever confidence < 0.70",
    }

    for target_dir in (BACKEND_MODELS_DIR, FRONTEND_MODELS_DIR):
        with open(target_dir / "crop_disease_labels.json", "w", encoding="utf-8") as f:
            json.dump(labels_payload, f, ensure_ascii=False, indent=2)

    print("Saved ONNX models and crop_disease_labels.json successfully.")


if __name__ == "__main__":
    main()
