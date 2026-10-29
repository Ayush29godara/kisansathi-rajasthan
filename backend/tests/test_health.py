"""Unit test for public health check endpoint."""

from fastapi.testclient import TestClient


def test_health_check_returns_200(client: TestClient):
    """Ensure /health returns 200 OK without requiring authentication."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert data["environment"] == "test"
