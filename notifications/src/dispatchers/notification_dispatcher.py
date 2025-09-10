from __future__ import annotations

"""
Notification Dispatcher (T076)

Purpose:
- Provide a small, focused orchestrator that sends messages to one or more
  channels (Telegram, Feishu) using the existing lightweight clients.
- Support optional Jinja2-based templating via TemplateEngine.

Scope:
- Implements only what is required for T076: a dispatcher class with a
  simple async `dispatch` entrypoint and basic per-channel routing.
- Advanced features (rate limiting, retries, queues) are handled by other
  components and are out of scope for this task.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import uuid

from templates.template_engine import TemplateEngine
from clients.telegram_client import TelegramClient
from clients.feishu_client import FeishuClient


_logger = logging.getLogger(__name__)


@dataclass
class DispatchResult:
    success: bool
    notification_id: str
    results: Dict[str, Dict[str, Any]]


class NotificationDispatcher:
    """Multi-channel notification dispatcher.

    - Renders message content from a template (optional)
    - Sends to one or more supported channels
    - Returns per-channel results and aggregate success flag
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        *,
        template_engine: Optional[TemplateEngine] = None,
    ) -> None:
        self.config = config or {}
        self.template_engine = template_engine or TemplateEngine()

        # Initialize channel clients from config blocks (if present)
        self.telegram = TelegramClient.from_config(self.config.get("telegram", {}))
        self.feishu = FeishuClient.from_config(self.config.get("feishu", {}))

    async def dispatch(
        self,
        *,
        channels: List[str],
        message: Optional[str] = None,
        template: Optional[str] = None,
        template_context: Optional[Dict[str, Any]] = None,
        template_name: Optional[str] = None,
        priority: Optional[str] = None,
        recipient_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Dispatch a notification to the provided channels.

        Inputs:
        - channels: list of channel names, e.g. ["telegram", "feishu"]
        - message: raw message to send (used if no template provided)
        - template: optional Jinja2 template string
        - template_context: optional context for rendering the template
        - template_name: alternatively render a named template (if registered)
        - priority: optional string; stored in result for caller visibility
        - recipient_id: optional recipient for API-based channels (Feishu)
        """

        notification_id = self._generate_id()

        # Prepare content
        content = message or ""
        if template or template_name:
            ctx = dict(template_context or {})
            ctx.setdefault("timestamp", datetime.utcnow().isoformat())
            try:
                if template:
                    content = self.template_engine.render(template, ctx, is_raw=True)
                else:
                    content = self.template_engine.render(template_name or "", ctx)
            except Exception as e:  # Defensive: TemplateEngine already guards errors
                _logger.error("Template rendering error", exc_info=True)
                content = f"Template rendering error: {e}"

        results: Dict[str, Dict[str, Any]] = {}
        overall_success = True

        for ch in channels:
            if ch == "telegram":
                res = await self.telegram.send_text(content)
                results[ch] = res
                overall_success = overall_success and bool(res.get("success"))
            elif ch == "feishu":
                # For webhook config, recipient_id is not required
                res = await self.feishu.send_text(content, recipient_id=recipient_id)
                results[ch] = res
                overall_success = overall_success and bool(res.get("success"))
            else:
                # Unknown channel
                results[ch] = {"success": False, "error": f"Unknown channel: {ch}"}
                overall_success = False

        return {
            "success": overall_success,
            "notification_id": notification_id,
            "results": results,
            "priority": priority or "medium",
            "channels": channels,
        }

    def _generate_id(self) -> str:
        return f"nd_{uuid.uuid4().hex[:12]}"


__all__ = ["NotificationDispatcher", "DispatchResult"]

