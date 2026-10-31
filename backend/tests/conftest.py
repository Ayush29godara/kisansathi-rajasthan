"""Pytest test configuration and shared fixtures."""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure repo root and backend directory are both in python sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for p in (repo_root, backend_root):
    if p not in sys.path:
        sys.path.insert(0, p)

# Set test environment flags before importing application modules
os.environ["ENVIRONMENT"] = "test"
os.environ["FRONTEND_ORIGIN"] = "http://localhost:5173"
os.environ["SUPABASE_JWT_SECRET"] = "mock_secret_for_unit_tests_only"

from app.main import app as fastapi_app
from app.db import Base, engine
from app import models  # ensure models are registered with Base

# Initialize in-memory test database schema
if engine is not None:
    Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Create a FastAPI TestClient instance."""
    return TestClient(fastapi_app)


@pytest.fixture
def auth_headers() -> dict:
    """Provide authentication headers with a mocked Supabase bearer token."""
    return {"Authorization": "Bearer mock_token_farmer_12345"}
