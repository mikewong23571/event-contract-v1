from __future__ import annotations

from typing import Any, Dict, Optional
import asyncio
import base64
import hashlib
import hmac
import logging
import time

import aiohttp


class FeishuClient:
    """Feishu (Lark) notification client.

    Supports two integration modes:
      1) Incoming Webhook (optionally signed with secret)
      2) Open API with app_id/app_secret and access token retrieval
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        *,
        secret: Optional[str] = None,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        request_timeout_seconds: int = 10,
    ) -> None:
        self.webhook_url = webhook_url
        self.secret = secret
        self.app_id = app_id
        self.app_secret = app_secret
        self.request_timeout_seconds = request_timeout_seconds

        self.logger = logging.getLogger(__name__)

        # Token cache (for app mode)
        self._access_token: Optional[str] = None
        self._token_expires_at: int = 0

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "FeishuClient":
        return cls(
            webhook_url=config.get("webhook_url"),
            secret=config.get("secret"),
            app_id=config.get("app_id"),
            app_secret=config.get("app_secret"),
            request_timeout_seconds=int(config.get("timeout_seconds", 10)),
        )

    async def send_text(
        self,
        message: str,
        *,
        recipient_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a plain text notification.

        If `webhook_url` is configured, uses webhook. Otherwise attempts Open API
        with app credentials and `recipient_id`.
        """

        if self.webhook_url:
            return await self._send_webhook({"msg_type": "text", "content": {"text": message}})
        if self.app_id and self.app_secret:
            if not recipient_id:
                return {"success": False, "error": "recipient_id required for API messages"}
            return await self._send_api(
                payload={
                    "receive_id": recipient_id,
                    "msg_type": "text",
                    "content": {"text": message},
                }
            )
        return {"success": False, "error": "Feishu not configured (webhook or app credentials required)"}

    async def send_card(
        self,
        card_content: Dict[str, Any],
        *,
        recipient_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send an interactive card message."""

        if self.webhook_url:
            return await self._send_webhook({"msg_type": "interactive", "card": card_content})
        if self.app_id and self.app_secret and recipient_id:
            return await self._send_api(
                payload={
                    "receive_id": recipient_id,
                    "msg_type": "interactive",
                    "content": card_content,
                }
            )
        return {"success": False, "error": "Insufficient configuration for card messages"}

    async def _send_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        assert self.webhook_url  # for type checkers

        # Add signature if secret configured
        if self.secret:
            ts = str(int(time.time()))
            payload.update({"timestamp": ts, "sign": self._generate_sign(ts)})

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=self.request_timeout_seconds,
                ) as resp:
                    data = await resp.json()
                    if resp.status == 200 and data.get("code") == 0:
                        return {"success": True, "response": data}
                    msg = data.get("msg", f"HTTP {resp.status}")
                    return {"success": False, "error": msg}
        except asyncio.TimeoutError:
            return {"success": False, "error": "Feishu webhook request timeout"}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"Feishu webhook error: {e}"}

    async def _send_api(self, *, payload: Dict[str, Any]) -> Dict[str, Any]:
        token_res = await self._get_access_token()
        if not token_res.get("success"):
            return token_res

        headers = {
            "Authorization": f"Bearer {token_res['access_token']}",
            "Content-Type": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://open.feishu.cn/open-apis/im/v1/messages",
                    json=payload,
                    headers=headers,
                    timeout=self.request_timeout_seconds,
                ) as resp:
                    data = await resp.json()
                    if resp.status == 200 and data.get("code") == 0:
                        return {"success": True, "response": data}
                    msg = data.get("msg", f"HTTP {resp.status}")
                    return {"success": False, "error": msg}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"Feishu API error: {e}"}

    async def _get_access_token(self) -> Dict[str, Any]:
        if not (self.app_id and self.app_secret):
            return {"success": False, "error": "App credentials not configured"}

        now = int(time.time())
        if self._access_token and now < self._token_expires_at - 300:
            return {"success": True, "access_token": self._access_token}

        body = {"app_id": self.app_id, "app_secret": self.app_secret}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
                    json=body,
                    timeout=self.request_timeout_seconds,
                ) as resp:
                    data = await resp.json()
                    if resp.status == 200 and data.get("code") == 0:
                        self._access_token = data.get("app_access_token")
                        expire = int(data.get("expire", 7200))
                        self._token_expires_at = now + expire
                        return {"success": True, "access_token": self._access_token}
                    msg = data.get("msg", f"HTTP {resp.status}")
                    return {"success": False, "error": f"Token error: {msg}"}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"Token request failed: {e}"}

    def _generate_sign(self, timestamp: str) -> str:
        # Per Feishu docs: base64(hmac_sha256(timestamp + "\n" + secret, empty-string))
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        return base64.b64encode(hmac_code).decode("utf-8")

    async def test_connection(self) -> Dict[str, Any]:
        """Basic connectivity check.

        - Webhook mode: send a small test message (not persisted)
        - App mode: fetch access token
        """

        if self.webhook_url:
            return await self._send_webhook({"msg_type": "text", "content": {"text": "🧪 Feishu test"}})
        if self.app_id and self.app_secret:
            return await self._get_access_token()
        return {"success": False, "error": "No configuration available for testing"}

    def validate_config(self) -> Dict[str, Any]:
        issues = []
        if not self.webhook_url and not (self.app_id and self.app_secret):
            issues.append("Either webhook_url or (app_id + app_secret) is required")
        if self.webhook_url and not self.webhook_url.startswith("https://open.feishu.cn/"):
            issues.append("webhook_url should start with https://open.feishu.cn/")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "config_present": {
                "webhook_url": bool(self.webhook_url),
                "secret": bool(self.secret),
                "app_id": bool(self.app_id),
                "app_secret": bool(self.app_secret),
            },
        }


__all__ = ["FeishuClient"]

