"""Pytest test configuration and shared fixtures."""

import os
import pytest
from fastapi.testclient import TestClient

# Set test environment flags before importing application modules
os.environ["ENVIRONMENT"] = "test"
os.environ["FRONTEND_ORIGIN"] = "http://localhost:5173"
os.environ["SUPABASE_JWT_SECRET"] = "mock_secret_for_unit_tests_only"

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Create a FastAPI TestClient instance."""
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict:
    """Provide authentication headers with a mocked Supabase bearer token."""
    return {"Authorization": "Bearer mock_token_farmer_12345"}
