import pytest

from src.websocket.connection_manager import ConnectionManager


class DummyWebSocket:
    def __init__(self):
        self.sent = []

    async def send_text(self, message: str) -> None:
        self.sent.append(message)


class FailingWebSocket(DummyWebSocket):
    async def send_text(self, message: str) -> None:  # type: ignore[override]
        raise RuntimeError("send failed")


@pytest.mark.asyncio
async def test_connect_and_active_count():
    manager = ConnectionManager()
    ws1 = DummyWebSocket()
    ws2 = DummyWebSocket()

    assert manager.active_count == 0

    await manager.connect(ws1)  # type: ignore[arg-type]
    assert manager.active_count == 1

    await manager.connect(ws2)  # type: ignore[arg-type]
    assert manager.active_count == 2


@pytest.mark.asyncio
async def test_disconnect_reduces_active_count():
    manager = ConnectionManager()
    ws = DummyWebSocket()

    await manager.connect(ws)  # type: ignore[arg-type]
    assert manager.active_count == 1

    manager.disconnect(ws)  # type: ignore[arg-type]
    assert manager.active_count == 0


@pytest.mark.asyncio
async def test_send_personal_message_calls_send_text():
    manager = ConnectionManager()
    ws = DummyWebSocket()

    await manager.connect(ws)  # type: ignore[arg-type]
    await manager.send_personal_message("hello", ws)  # type: ignore[arg-type]

    assert ws.sent == ["hello"]


@pytest.mark.asyncio
async def test_broadcast_sends_to_all_and_prunes_failing_connections():
    manager = ConnectionManager()
    ok_ws1 = DummyWebSocket()
    ok_ws2 = DummyWebSocket()
    failing_ws = FailingWebSocket()

    await manager.connect(ok_ws1)  # type: ignore[arg-type]
    await manager.connect(ok_ws2)  # type: ignore[arg-type]
    await manager.connect(failing_ws)  # type: ignore[arg-type]

    await manager.broadcast("ping")

    # Both healthy connections received the message
    assert ok_ws1.sent == ["ping"]
    assert ok_ws2.sent == ["ping"]

    # Failing connection should have been removed
    assert manager.active_count == 2