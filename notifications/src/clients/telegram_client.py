from __future__ import annotations

from typing import Any, Dict, Optional
import asyncio
import logging

import aiohttp


class TelegramClient:
    """Minimal Telegram Bot API client for sending notifications.

    This client intentionally focuses on the core capabilities required by
    the notifications service for T073:
      - Send text messages to a target chat
      - Validate configuration and test connectivity

    Implementation uses Telegram HTTP Bot API directly via `aiohttp` to
    avoid heavyweight runtime dependencies and to keep the surface area small.
    """

    def __init__(
        self,
        bot_token: Optional[str],
        default_chat_id: Optional[str] = None,
        *,
        default_parse_mode: str = "Markdown",
        request_timeout_seconds: int = 10,
    ) -> None:
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id
        self.default_parse_mode = default_parse_mode
        self.request_timeout_seconds = request_timeout_seconds

        self.logger = logging.getLogger(__name__)
        self._api_base = (
            f"https://api.telegram.org/bot{self.bot_token}"
            if self.bot_token
            else None
        )

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "TelegramClient":
        """Construct from a simple dict-like config.

        Expected keys:
          - bot_token: str
          - default_chat_id: Optional[str]
          - parse_mode: Optional[str]
          - timeout_seconds: Optional[int]
        """

        return cls(
            bot_token=config.get("bot_token"),
            default_chat_id=config.get("default_chat_id") or config.get("chat_id"),
            default_parse_mode=config.get("parse_mode", "Markdown"),
            request_timeout_seconds=int(config.get("timeout_seconds", 10)),
        )

    async def send_text(
        self,
        message: str,
        *,
        chat_id: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: bool = False,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Send a text message to Telegram.

        Returns a dict with at minimum `success: bool`. On success includes
        `message_id` and `chat_id`; on failure includes `error`.
        """

        if not self.bot_token or not self._api_base:
            return {"success": False, "error": "Telegram bot token not configured"}

        target_chat = chat_id or self.default_chat_id
        if not target_chat:
            return {"success": False, "error": "No chat ID specified"}

        url = f"{self._api_base}/sendMessage"
        payload = {
            "chat_id": target_chat,
            "text": message,
            "parse_mode": parse_mode or self.default_parse_mode,
            "disable_notification": disable_notification,
        }

        req_timeout = int(timeout_seconds or self.request_timeout_seconds)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=req_timeout) as resp:
                    data = await resp.json()
                    if resp.status == 200 and data.get("ok"):
                        result = data.get("result", {})
                        return {
                            "success": True,
                            "message_id": result.get("message_id"),
                            "chat_id": target_chat,
                        }
                    desc = data.get("description", f"HTTP {resp.status}")
                    return {"success": False, "error": desc}
        except asyncio.TimeoutError:
            return {"success": False, "error": "Telegram API request timeout"}
        except Exception as e:  # noqa: BLE001 - want clear error through boundary
            return {"success": False, "error": f"Telegram send error: {e}"}

    async def test_connection(self) -> Dict[str, Any]:
        """Validate bot token by calling getMe."""

        if not self.bot_token or not self._api_base:
            return {"success": False, "error": "Bot token not configured"}

        url = f"{self._api_base}/getMe"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.request_timeout_seconds) as resp:
                    data = await resp.json()
                    if resp.status == 200 and data.get("ok"):
                        info = data.get("result", {})
                        return {
                            "success": True,
                            "bot_info": {
                                "id": info.get("id"),
                                "username": info.get("username"),
                                "first_name": info.get("first_name"),
                                "is_bot": info.get("is_bot"),
                            },
                        }
                    desc = data.get("description", f"HTTP {resp.status}")
                    return {"success": False, "error": desc}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": str(e)}

    def validate_config(self) -> Dict[str, Any]:
        """Return validation summary for the current configuration."""

        issues = []
        if not self.bot_token:
            issues.append("bot_token is required")
        if not self.default_chat_id:
            issues.append("default_chat_id is recommended")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "config_present": {
                "bot_token": bool(self.bot_token),
                "default_chat_id": bool(self.default_chat_id),
            },
        }


__all__ = ["TelegramClient"]

