"""WebSocket Connection Manager (T056)

Provides minimal connection management utilities for WebSocket endpoints.

Scope (T056):
- Maintain a registry of active WebSocket connections
- Support adding and removing connections
- Support sending a message to a single connection
- Support broadcasting a message to all active connections

This module is intentionally generic and does not couple to specific
endpoints. Handlers remain responsible for accepting connections.
"""
from __future__ import annotations

from typing import Set

try:
    # Prefer starlette type annotations if available at runtime
    from starlette.websockets import WebSocket  # type: ignore
except Exception:  # pragma: no cover - typings only
    WebSocket = object  # type: ignore


class ConnectionManager:
    """Manage active WebSocket connections.

    Tracks active connections and provides helpers to send messages
    to one or all connections.
    """

    def __init__(self) -> None:
        self._active_connections: Set[WebSocket] = set()

    @property
    def active_count(self) -> int:
        """Return the number of active WebSocket connections."""
        return len(self._active_connections)

    async def connect(self, websocket: WebSocket) -> None:
        """Register a WebSocket connection.

        Note: The caller is responsible for `websocket.accept()`.
        """
        self._active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection if present."""
        self._active_connections.discard(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """Send a text message to a single WebSocket connection."""
        await websocket.send_text(message)

    async def broadcast(self, message: str) -> None:
        """Broadcast a text message to all active WebSocket connections.

        If sending fails for a connection (e.g., closed), it will be removed
        from the registry.
        """
        # Snapshot to avoid issues if the set changes during iteration
        for connection in list(self._active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                # Remove problematic/closed connections
                self._active_connections.discard(connection)