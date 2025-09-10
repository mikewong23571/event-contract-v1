import asyncio
from typing import Any, Dict

import pytest


# The tests import from the notifications src tree via package layout
from dispatchers.notification_dispatcher import NotificationDispatcher  # type: ignore


@pytest.mark.asyncio
async def test_dispatch_with_template_and_channels_success(monkeypatch):
    # Arrange: stub Telegram and Feishu clients to avoid network IO
    async def _ok_send_text(self, message: str, **kwargs) -> Dict[str, Any]:  # noqa: ANN001
        return {"success": True, "echo": message}

    # Patch client methods
    import clients.telegram_client as tg_mod  # type: ignore
    import clients.feishu_client as feishu_mod  # type: ignore

    monkeypatch.setattr(tg_mod.TelegramClient, "send_text", _ok_send_text, raising=True)
    monkeypatch.setattr(feishu_mod.FeishuClient, "send_text", _ok_send_text, raising=True)

    dispatcher = NotificationDispatcher(
        config={
            "telegram": {"bot_token": "x", "default_chat_id": "-1001"},
            "feishu": {"webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/mock"},
        }
    )

    template = "**New Signal**\nSymbol: {{ symbol }}\nDirection: {{ direction }}"
    data = {"symbol": "BTCUSDT", "direction": "UP"}

    # Act
    res = await dispatcher.dispatch(
        channels=["telegram", "feishu"],
        template=template,
        template_context=data,
        priority="high",
    )

    # Assert
    assert res["success"] is True
    assert set(res["results"].keys()) == {"telegram", "feishu"}
    # Message should be rendered (placeholders replaced)
    assert res["results"]["telegram"]["success"] is True
    assert "BTCUSDT" in res["results"]["telegram"]["echo"]


@pytest.mark.asyncio
async def test_dispatch_unknown_channel(monkeypatch):
    dispatcher = NotificationDispatcher(config={})
    res = await dispatcher.dispatch(
        message="Hello",
        channels=["unknown"],
    )
    assert res["success"] is False
    assert "unknown" in res["results"]
    assert res["results"]["unknown"]["success"] is False

