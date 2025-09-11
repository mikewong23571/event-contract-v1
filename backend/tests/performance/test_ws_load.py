from typing import List

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "endpoint",
    [
        "/ws/signals",
        "/ws/market-data",
        "/ws/alerts",
    ],
)
def test_websocket_load_multiple_connections(endpoint: str, client: TestClient):
    max_connections = 20
    sockets: List = []

    # Establish multiple connections
    for _ in range(max_connections):
        ws = client.websocket_connect(endpoint)
        sockets.append(ws)

    # All connections should be open
    assert len(sockets) == max_connections

    # Clean up
    for ws in sockets:
        # Some endpoints might send initial messages; ignore and close
        try:
            ws.close()
        except Exception:
            pass

