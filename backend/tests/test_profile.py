"""Unit and integration tests for Profile and Farm endpoints."""

from fastapi.testclient import TestClient


def test_get_profile_unauthenticated_fails(client: TestClient):
    """GET /profile without token must return 401."""
    response = client.get("/profile")
    assert response.status_code == 401


def test_get_profile_authenticated_succeeds(client: TestClient, auth_headers: dict):
    """GET /profile with valid token returns user profile."""
    response = client.get("/profile", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert data["language"] in ("hi", "en")


def test_put_profile_updates_language(client: TestClient, auth_headers: dict):
    """PUT /profile updates language preference."""
    response = client.put("/profile", json={"language": "en"}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"


def test_put_profile_updates_farm(client: TestClient, auth_headers: dict):
    """PUT /profile updates farm parameters."""
    farm_update = {
        "farm": {
            "district": "Kota",
            "tehsil": "Digod",
            "crop": "Soybean",
            "land_hectare": 3.5,
            "irrigation": "canal",
            "sowing_date": "2026-07-10",
        }
    }
    response = client.put("/profile", json=farm_update, headers=auth_headers)
    assert response.status_code == 200


def test_create_farm_unauthenticated_fails(client: TestClient):
    """POST /farms without token must return 401."""
    response = client.post(
        "/farms",
        json={
            "district": "Alwar",
            "tehsil": "Ramgarh",
            "crop": "Mustard",
            "land_hectare": 2.0,
            "irrigation": "tubewell",
            "sowing_date": "2026-10-15",
        },
    )
    assert response.status_code == 401


def test_create_farm_authenticated_succeeds(client: TestClient, auth_headers: dict):
    """POST /farms with valid token creates farm profile."""
    response = client.post(
        "/farms",
        json={
            "district": "Alwar",
            "tehsil": "Ramgarh",
            "crop": "Mustard",
            "land_hectare": 2.0,
            "irrigation": "tubewell",
            "sowing_date": "2026-10-15",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["district"] == "Alwar"
    assert data["crop"] == "Mustard"
    assert data["land_hectare"] == 2.0
