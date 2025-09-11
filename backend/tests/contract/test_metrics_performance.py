"""
Contract tests for GET /api/v1/metrics/performance
"""
from fastapi.testclient import TestClient
from src.main import app


client = TestClient(app)


def test_get_performance_metrics_basic():
    resp = client.get("/api/v1/metrics/performance")
    assert resp.status_code == 200
    data = resp.json()
    assert "metrics" in data and isinstance(data["metrics"], list)
    assert "summary" in data and isinstance(data["summary"], dict)


def test_get_performance_metrics_bad_dates():
    resp1 = client.get("/api/v1/metrics/performance?start_date=2024-13-01")
    assert resp1.status_code in [400, 422]  # explicit 400 expected, allow 422
    resp2 = client.get("/api/v1/metrics/performance?end_date=not-a-date")
    assert resp2.status_code in [400, 422]

