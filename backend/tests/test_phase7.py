"""Unit and integration tests for Phase 7 features:
- System metadata endpoint (/system/metadata)
- Feedback recording (/feedback)
- Chat interaction history timeline (/history)
- Rate limiting unit logic
- Structured logging & X-Request-ID header injection
"""

import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.rate_limiter import SlidingWindowRateLimiter


def test_system_metadata_endpoint():
    """Verify /system/metadata returns real metrics, data sources, and limitations."""
    client = TestClient(app)
    response = client.get("/system/metadata")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "KisanSathi Rajasthan"
    assert "modules" in data
    assert len(data["modules"]) >= 4

    # Verify Yield module transparency
    yield_module = next((m for m in data["modules"] if "Yield" in m["module"]), None)
    assert yield_module is not None
    assert "LOYO MAE" in yield_module["accuracy_metric"]
    assert "Directorate of Economics & Statistics" in yield_module["data_source"]
    assert len(yield_module["limitations"]) > 0

    # Verify Weather / FAO-56 module transparency
    weather_mod = next((m for m in data["modules"] if "Irrigation" in m["module"] or "मौसम" in m["module"]), None)
    assert weather_mod is not None
    assert "Penman-Monteith" in weather_mod["model_type"]


def test_structured_logging_injects_x_request_id():
    """Verify that every HTTP response includes an X-Request-ID header."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 10


def test_sliding_window_rate_limiter_unit():
    """Directly test sliding window rate limiter logic."""
    limiter = SlidingWindowRateLimiter(times=3, seconds=2)
    key = "test_user_ip"

    # First 3 requests permitted
    assert limiter.is_rate_limited(key) is False
    assert limiter.is_rate_limited(key) is False
    assert limiter.is_rate_limited(key) is False

    # 4th request within 2 seconds rejected
    assert limiter.is_rate_limited(key) is True

    # Test reset
    limiter.clear()
    assert limiter.is_rate_limited(key) is False


def test_feedback_submission(client, auth_headers):
    """Verify farmer feedback can be submitted for an advisory response."""
    # Positive rating
    resp = client.post(
        "/feedback",
        headers=auth_headers,
        json={"message_id": "test-msg-123", "rating": 1, "actual_outcome": "सरसों में सफेद रोली नियंत्रण में रही।"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "recorded"


def test_history_endpoint(client, auth_headers):
    """Verify farmer can retrieve chat & advisory history."""
    resp = client.get("/history?limit=10&offset=0", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
