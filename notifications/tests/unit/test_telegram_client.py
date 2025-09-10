import os
import sys
import types
import asyncio

import pytest


sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from clients.telegram_client import TelegramClient  # type: ignore  # noqa: E402


class _DummyResponse:
    def __init__(self, status: int, payload: dict):
        self.status = status
        self._payload = payload

    async def json(self):
        await asyncio.sleep(0)
        return self._payload


class _DummyPostCtx:
    def __init__(self, response: _DummyResponse):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _DummySession:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def post(self, url, json=None, timeout=None):  # noqa: A002 - shadow builtins ok in tests
        # Simulate success for sendMessage
        payload = {"ok": True, "result": {"message_id": 12345}}
        return _DummyPostCtx(_DummyResponse(200, payload))

    def get(self, url, timeout=None):
        # Simulate success for getMe
        payload = {"ok": True, "result": {"id": 1, "username": "bot", "first_name": "Test", "is_bot": True}}
        return _DummyPostCtx(_DummyResponse(200, payload))


@pytest.mark.asyncio
async def test_telegram_client_validate_config():
    client = TelegramClient(bot_token=None)
    res = client.validate_config()
    assert not res["valid"]
    assert "bot_token" in ",".join(res["issues"]).lower()


@pytest.mark.asyncio
async def test_telegram_client_send_text_success(monkeypatch):
    # Patch aiohttp.ClientSession with our dummy
    import clients.telegram_client as mod  # type: ignore

    monkeypatch.setattr(mod, "aiohttp", types.SimpleNamespace(ClientSession=_DummySession))

    client = TelegramClient(bot_token="mock_token", default_chat_id="-1001")
    res = await client.send_text("hello world")
    assert res["success"] is True
    assert res["message_id"] == 12345


@pytest.mark.asyncio
async def test_telegram_client_test_connection(monkeypatch):
    import clients.telegram_client as mod  # type: ignore

    monkeypatch.setattr(mod, "aiohttp", types.SimpleNamespace(ClientSession=_DummySession))

    client = TelegramClient(bot_token="mock_token")
    res = await client.test_connection()
    assert res["success"] is True
    assert "bot_info" in res

