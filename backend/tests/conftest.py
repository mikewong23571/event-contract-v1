"""
Pytest configuration and shared fixtures for backend tests.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_headers():
    """Common headers for API requests."""
    return {"Content-Type": "application/json"}