"""Unit and integration tests for Crop Disease Diagnosis and Advice Pipeline."""

import io
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

from services.disease_service import (
    sanitize_and_strip_exif,
    get_disease_advice_from_kb,
    CONFIDENCE_THRESHOLD,
    VERIFIED_DISEASE_KB,
)
from scripts.prepare_disease_dataset import (
    compute_sha256,
    compute_dhash,
    detect_duplicate_clusters,
    partition_clusters,
)


def create_sample_image_bytes(format: str = "JPEG", size: tuple = (100, 100), color: tuple = (34, 139, 34)) -> bytes:
    """Helper to generate in-memory dummy image bytes."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


def test_sanitize_and_strip_exif_valid():
    """Verify that EXIF stripping returns valid sanitized image bytes."""
    valid_bytes = create_sample_image_bytes()
    cleaned = sanitize_and_strip_exif(valid_bytes)
    assert len(cleaned) > 0
    # Cleaned image can be reopened and has no EXIF dict
    reopened = Image.open(io.BytesIO(cleaned))
    assert reopened.format in ("JPEG", "PNG")
    assert getattr(reopened, "_getexif", lambda: None)() is None


def test_sanitize_and_strip_exif_invalid_format():
    """Verify non-image bytes raise ValueError."""
    with pytest.raises(ValueError, match="Corrupt or invalid image"):
        sanitize_and_strip_exif(b"this is not an image file")


def test_disease_advice_high_confidence():
    """Verify high-confidence recognized disease returns verified KB advice with citations."""
    res = get_disease_advice_from_kb(crop="Mustard", predicted_label="mustard_white_rust", confidence=0.88)
    assert not res.is_fallback
    assert res.confidence == 0.88
    assert "White Rust" in res.predicted_label or "सफेद रोली" in res.predicted_label
    assert "मैनकोजेब" in res.treatment_advice
    assert len(res.sources) > 0
    assert "Kota" in res.sources[0].source or "AU" in res.sources[0].source


def test_disease_advice_low_confidence_triggers_kvk_rule():
    """CRITICAL RULE: Confidence < 0.70 must fall back to KVK referral."""
    res = get_disease_advice_from_kb(crop="Mustard", predicted_label="mustard_white_rust", confidence=0.58)
    assert res.is_fallback
    assert res.confidence == 0.58
    assert "KVK" in res.treatment_advice or "कृषि विज्ञान केंद्र" in res.treatment_advice
    assert len(res.sources) == 0


def test_disease_advice_healthy_crop():
    """Verify healthy crop confirmation requires no pesticide."""
    res = get_disease_advice_from_kb(crop="Mustard", predicted_label="mustard_healthy", confidence=0.92)
    assert not res.is_fallback
    assert "स्वस्थ" in res.predicted_label
    assert "आवश्यकता नहीं" in res.treatment_advice


def test_disease_advice_tomato_early_blight():
    """Verify Tomato Early Blight returns authentic AU Kota POP advice."""
    res = get_disease_advice_from_kb(crop="Tomato", predicted_label="tomato_early_blight", confidence=0.89)
    assert not res.is_fallback
    assert "Early Blight" in res.predicted_label or "झुलसा" in res.predicted_label
    assert "मैनकोजेब" in res.treatment_advice
    assert len(res.sources) > 0


def test_disease_advice_fuzzy_synonym_normalization():
    """Verify shortened or fuzzy synonyms (e.g. 'white_rust', 'early_blight') normalize accurately."""
    res = get_disease_advice_from_kb(crop="Mustard", predicted_label="white_rust", confidence=0.85)
    assert not res.is_fallback
    assert "White Rust" in res.predicted_label

    res_tomato = get_disease_advice_from_kb(crop="Tomato", predicted_label="early_blight", confidence=0.88)
    assert not res_tomato.is_fallback
    assert "Early Blight" in res_tomato.predicted_label


def create_textured_image(pattern: str = "vertical") -> Tuple[bytes, Image.Image]:
    """Helper to generate textured leaf-like images with distinct perceptual hashes."""
    img = Image.new("RGB", (100, 100), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    if pattern == "vertical":
        for x in range(0, 100, 15):
            draw.line([(x, 0), (x, 100)], fill=(20, 120, 20), width=5)
    else:
        for y in range(0, 100, 15):
            draw.line([(0, y), (100, y)], fill=(120, 20, 20), width=5)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue(), img


def test_duplicate_detection_and_non_leaking_split():
    """Verify duplicate images are clustered together and never leaked across splits."""
    img1_bytes, pil1 = create_textured_image(pattern="vertical")
    # img2 is an exact duplicate of img1
    img2_bytes = img1_bytes
    # img3 has horizontal stripes (completely different pattern)
    img3_bytes, pil3 = create_textured_image(pattern="horizontal")

    entries = [
        {"id": "1", "filename": "a.jpg", "sha256": compute_sha256(img1_bytes), "dhash": compute_dhash(pil1)},
        {"id": "2", "filename": "b_dup.jpg", "sha256": compute_sha256(img2_bytes), "dhash": compute_dhash(pil1)},
        {"id": "3", "filename": "c.jpg", "sha256": compute_sha256(img3_bytes), "dhash": compute_dhash(pil3)},
    ]

    clusters = detect_duplicate_clusters(entries)
    # img1 and img2 must be grouped in the same cluster, img3 in a separate cluster
    assert len(clusters) == 2
    dup_cluster = next(c for c in clusters if len(c) == 2)
    ids_in_dup_cluster = {item["id"] for item in dup_cluster}
    assert ids_in_dup_cluster == {"1", "2"}

    # Partition clusters
    assigned = partition_clusters(clusters, train_ratio=0.5, val_ratio=0.25, seed=42)
    split_map = {item["id"]: item["split"] for item in assigned}

    # Strict non-leakage assertion: img1 and img2 MUST have the exact same split!
    assert split_map["1"] == split_map["2"]


def test_api_diagnose_unauthenticated_fails(client: TestClient):
    """POST /diagnose must require authentication."""
    img_bytes = create_sample_image_bytes()
    response = client.post(
        "/diagnose",
        data={"crop": "Mustard", "opt_in_store": "false"},
        files={"file": ("leaf.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 401


def test_api_diagnose_rejects_non_image(client: TestClient, auth_headers: dict):
    """POST /diagnose must reject text files."""
    response = client.post(
        "/diagnose",
        data={"crop": "Mustard", "opt_in_store": "false"},
        files={"file": ("test.txt", b"plain text", "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "Only JPEG and PNG" in response.json()["detail"]


def test_api_diagnose_fallback_authenticated_succeeds(client: TestClient, auth_headers: dict):
    """POST /diagnose authenticated fallback runs and returns diagnosis schema."""
    img_bytes = create_sample_image_bytes()
    response = client.post(
        "/diagnose",
        data={"crop": "Mustard", "opt_in_store": "true"},
        files={"file": ("leaf.jpg", img_bytes, "image/jpeg")},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["crop"] == "Mustard"
    assert "predicted_label" in data
    assert "confidence" in data
    assert data["confidence"] > 0
    assert "treatment_advice" in data
    assert "disclaimer" in data


def test_api_advice_disease_high_confidence(client: TestClient, auth_headers: dict):
    """POST /advice/disease returns verified treatment from KB."""
    payload = {
        "crop": "Mustard",
        "predicted_label": "mustard_white_rust",
        "confidence": 0.84,
        "model_version": "onnx-mobilenet-v3",
    }
    response = client.post("/advice/disease", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert not data["is_fallback"]
    assert "मैनकोजेब" in data["treatment_advice"]
    assert len(data["sources"]) > 0


def test_api_advice_disease_low_confidence_kvk_referral(client: TestClient, auth_headers: dict):
    """POST /advice/disease with confidence < 0.70 must enforce KVK referral."""
    payload = {
        "crop": "Bajra",
        "predicted_label": "bajra_blast",
        "confidence": 0.55,
        "model_version": "onnx-mobilenet-v3",
    }
    response = client.post("/advice/disease", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_fallback"]
    assert "KVK" in data["treatment_advice"] or "कृषि विज्ञान केंद्र" in data["treatment_advice"]
