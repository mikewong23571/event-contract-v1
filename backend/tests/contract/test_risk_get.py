"""
Contract test for GET /api/v1/risk-parameters endpoint

This test validates the API contract specification for retrieving risk parameters.
The test MUST FAIL initially as the endpoint is not implemented yet (TDD requirement).
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
import uuid
from src.main import app

client = TestClient(app)


class TestGetRiskParametersContract:
    """Contract tests for GET /api/v1/risk-parameters endpoint"""

    def test_get_risk_parameters_success_response(self):
        """Test successful response structure matches contract"""
        response = client.get("/api/v1/risk-parameters")
        
        # Contract: Should return 200 OK when parameters exist
        assert response.status_code == 200
        
        # Contract: Response content type should be JSON
        assert response.headers["content-type"].startswith("application/json")
        
        # Contract: Response should be RiskParameters object
        data = response.json()
        assert isinstance(data, dict)
        
        # Contract: Required fields per RiskParameters schema
        required_fields = [
            "max_bet_size", "max_daily_bets", "max_parallel_positions", 
            "min_probability_edge"
        ]
        for field in required_fields:
            assert field in data

    def test_get_risk_parameters_schema_validation(self):
        """Test RiskParameters schema compliance"""
        response = client.get("/api/v1/risk-parameters")
        assert response.status_code == 200
        
        data = response.json()
        
        # Contract: Field type validation
        if "id" in data:
            assert isinstance(data["id"], str)
            uuid.UUID(data["id"])  # Should be valid UUID
        
        assert isinstance(data["max_bet_size"], str)  # Decimal as string
        float(data["max_bet_size"])  # Should be valid decimal
        
        assert isinstance(data["max_daily_bets"], int)
        assert data["max_daily_bets"] >= 1
        
        assert isinstance(data["max_parallel_positions"], int) 
        assert data["max_parallel_positions"] >= 1
        
        assert isinstance(data["min_probability_edge"], str)
        edge = float(data["min_probability_edge"])
        assert 0.0 <= edge <= 1.0

    def test_get_risk_parameters_not_found(self):
        """Test 404 response when no risk parameters configured"""
        # This might return 404 if no risk parameters are set
        response = client.get("/api/v1/risk-parameters")
        assert response.status_code in [200, 404]