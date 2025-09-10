"""
Contract test for PUT /api/v1/risk-parameters endpoint

This test validates the API contract specification for updating risk parameters.
The test MUST FAIL initially as the endpoint is not implemented yet (TDD requirement).
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestPutRiskParametersContract:
    """Contract tests for PUT /api/v1/risk-parameters endpoint"""

    def test_put_risk_parameters_success_response(self):
        """Test successful update response structure"""
        request_body = {
            "max_bet_size": "100.00",
            "max_daily_bets": 10,
            "max_parallel_positions": 3,
            "min_probability_edge": "0.05"
        }
        
        response = client.put("/api/v1/risk-parameters", json=request_body)
        
        # Contract: Should return 200 OK for successful update
        assert response.status_code == 200
        
        # Contract: Response content type should be JSON
        assert response.headers["content-type"].startswith("application/json")
        
        # Contract: Response should be updated RiskParameters object
        data = response.json()
        assert isinstance(data, dict)
        assert "max_bet_size" in data
        assert "max_daily_bets" in data

    def test_put_risk_parameters_validation(self):
        """Test request validation per RiskParametersUpdate schema"""
        # Valid request
        valid_request = {
            "max_bet_size": "50.00",
            "max_daily_bets": 5,
            "max_parallel_positions": 2,
            "min_probability_edge": "0.10"
        }
        response = client.put("/api/v1/risk-parameters", json=valid_request)
        assert response.status_code == 200
        
        # Invalid values should return 400
        invalid_requests = [
            {"max_daily_bets": 0},  # Below minimum
            {"max_parallel_positions": 0},  # Below minimum
            {"min_probability_edge": "invalid"}  # Invalid format
        ]
        
        for invalid_request in invalid_requests:
            response = client.put("/api/v1/risk-parameters", json=invalid_request)
            assert response.status_code == 400

    def test_put_risk_parameters_partial_update(self):
        """Test partial update capability"""
        # Should allow updating only some fields
        partial_update = {"max_bet_size": "200.00"}
        response = client.put("/api/v1/risk-parameters", json=partial_update)
        assert response.status_code == 200