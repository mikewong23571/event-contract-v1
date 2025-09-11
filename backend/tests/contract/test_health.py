"""
Tests for health endpoints
"""
import pytest
from fastapi.testclient import TestClient

from src.main import app


class TestHealthContract:
    """Test health endpoint contract compliance."""

    def test_health_endpoint_api_v1(self):
        """Test health endpoint at /api/v1/health."""
        with TestClient(app) as client:
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "status" in data
            assert "checks" in data
            assert "timestamp" in data
            assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_endpoint_v1_compatibility(self):
        """Test health endpoint at /v1/health for compatibility."""
        with TestClient(app) as client:
            response = client.get("/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "status" in data
            assert "checks" in data  
            assert "timestamp" in data
            assert data["status"] in ["healthy", "degraded", "unhealthy"]
            
    def test_health_endpoint_response_format(self):
        """Test health endpoint response format."""
        with TestClient(app) as client:
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            
            # Check required fields
            assert isinstance(data["status"], str)
            assert isinstance(data["checks"], dict)
            assert isinstance(data["timestamp"], str)
            
            # Check checks structure
            checks = data["checks"]
            expected_checks = {"database", "market_data_feed", "signal_generation"}
            assert set(checks.keys()) == expected_checks
            
            for check_name, check_status in checks.items():
                assert check_status in ["ok", "error"]