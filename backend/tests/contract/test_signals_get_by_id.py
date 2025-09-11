"""
Contract tests for GET /api/v1/signals/{signal_id}
"""
from fastapi.testclient import TestClient
from src.main import app
import uuid


client = TestClient(app)


def test_get_signal_by_id_success():
    # Create a signal first
    create = client.post("/api/v1/signals/generate", json={"symbol": "BTCUSDT"})
    assert create.status_code == 201
    sig = create.json()
    signal_id = sig["id"]

    resp = client.get(f"/api/v1/signals/{signal_id}")
    assert resp.status_code == 200
    data = resp.json()
    # Basic schema checks
    assert data["id"] == signal_id
    assert data["symbol"] == "BTCUSDT"
    assert data["direction"] in ["UP", "DOWN"]
    assert 0.0 <= float(data["predicted_probability"]) <= 1.0


def test_get_signal_by_id_not_found():
    unknown_id = str(uuid.uuid4())
    resp = client.get(f"/api/v1/signals/{unknown_id}")
    assert resp.status_code == 404


def test_get_signal_by_id_invalid_uuid():
    resp = client.get("/api/v1/signals/not-a-uuid")
    assert resp.status_code == 400

