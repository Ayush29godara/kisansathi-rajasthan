"""Unit tests for Supabase JWT verification and endpoint security."""

from fastapi.testclient import TestClient


def test_protected_endpoint_without_token_fails(client: TestClient):
    """Ensure accessing protected endpoint without token returns 401 Unauthorized."""
    response = client.get("/profile")
    assert response.status_code == 401
    assert "Authorization header missing" in response.json()["detail"]


def test_protected_endpoint_with_invalid_token_fails(client: TestClient):
    """Ensure malformed or unauthorized token returns 401."""
    response = client.get(
        "/profile",
        headers={"Authorization": "Bearer invalid_gibberish_token"}
    )
    assert response.status_code == 401


def test_protected_endpoint_with_mock_token_succeeds(client: TestClient, auth_headers: dict):
    """Ensure authenticated request with valid token succeeds."""
    response = client.get("/profile", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "farmer_12345"
    assert data["language"] == "hi"
