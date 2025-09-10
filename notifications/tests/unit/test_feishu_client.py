import os
import sys
import types
import asyncio

import pytest


sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from clients.feishu_client import FeishuClient  # type: ignore  # noqa: E402


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

    def post(self, url, json=None, headers=None, timeout=None):  # noqa: A002 - shadow builtins ok in tests
        # Always return success structure used by Feishu
        payload = {"code": 0, "msg": "ok", "data": {"message_id": "mid-1"}}
        return _DummyPostCtx(_DummyResponse(200, payload))


def test_feishu_client_validate_config():
    client = FeishuClient()
    res = client.validate_config()
    assert not res["valid"]
    assert "required" in ",".join(res["issues"]).lower()


@pytest.mark.asyncio
async def test_feishu_client_webhook_send(monkeypatch):
    import clients.feishu_client as mod  # type: ignore

    monkeypatch.setattr(mod, "aiohttp", types.SimpleNamespace(ClientSession=_DummySession))

    client = FeishuClient(webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/mock")
    res = await client.send_text("hi")
    assert res["success"] is True


@pytest.mark.asyncio
async def test_feishu_client_api_send(monkeypatch):
    import clients.feishu_client as mod  # type: ignore

    monkeypatch.setattr(mod, "aiohttp", types.SimpleNamespace(ClientSession=_DummySession))

    client = FeishuClient(app_id="app", app_secret="secret")
    res = await client.send_text("hi", recipient_id="ou_123")
    assert res["success"] is True

