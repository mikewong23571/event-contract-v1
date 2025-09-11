"""
End-to-end tests for the trading workflow:
- Generate a signal via API
- Retrieve signals via API
- Verify WebSocket channel can be used for signals
"""

from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient


def test_end_to_end_signal_generation_flow(client: TestClient, sample_headers: Dict[str, str]):
    # 1) Generate a signal for a symbol
    payload = {"symbol": "BTCUSDT", "expiry_minutes": 5}
    resp = client.post("/api/v1/signals/generate", json=payload, headers=sample_headers)
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert "signal_id" in data

    # 2) Retrieve signals list
    resp2 = client.get("/api/v1/signals", headers=sample_headers)
    assert resp2.status_code == 200
    body = resp2.json()
    assert isinstance(body, list)
    if body:
        first = body[0]
        # Minimal contract checks
        for k in ("symbol", "direction", "predicted_probability"):
            assert k in first


def test_end_to_end_websocket_signals_channel(client: TestClient):
    # Verify that WS signals channel can be connected to as part of e2e
    with client.websocket_connect("/ws/signals") as ws:
        # No strict messaging here; just ensure connection is established
        assert ws is not None

