"""
Contract test for WebSocket /ws/alerts

This test validates the WebSocket contract for subscribing to trading alerts.
The test MUST FAIL initially as the WebSocket endpoint is not implemented yet (TDD requirement).
"""

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestWebSocketAlertsContract:
    """Contract tests for WebSocket /ws/alerts"""

    def test_websocket_alerts_connection_success(self):
        """Connection to alerts channel should succeed (per contract)."""
        with client.websocket_connect("/ws/alerts") as ws:
            assert ws is not None

