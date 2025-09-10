from __future__ import annotations

"""
NotificationService

Service-layer wrapper for notification operations used by the backend API.

Scope (T044):
- Provide a cohesive interface for configuring channels and templates
- Offer simple dispatch, history, and stats utilities
- Keep implementation self-contained (no cross-component imports)

Notes:
- This class intentionally does not integrate external networks or the
  notifications component. Later tasks handle inter-service messaging and
  API endpoints that call into this service.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import logging
import re
import asyncio


class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


@dataclass
class NotificationRecord:
    id: str
    message: str
    channels: List[str]
    priority: NotificationPriority
    created_at: datetime
    status: NotificationStatus = NotificationStatus.PENDING
    attempts: int = 0
    results: Dict[str, Any] = field(default_factory=dict)


class NotificationService:
    """Backend notification service façade.

    Responsibilities:
    - Manage channel configuration
    - Manage and render templates
    - Dispatch notifications (in-memory simulation)
    - Maintain basic history and stats for inspection

    This implementation is purposely minimal and self-contained to satisfy
    T044 without introducing cross-component dependencies. Downstream tasks
    can replace the send logic with real messaging integration.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.logger = logging.getLogger(__name__)
        self.config: Dict[str, Any] = config or {}

        # Channels and templates are stored in-memory for now
        self._channels: Dict[str, Dict[str, Any]] = {}
        self._templates: Dict[str, str] = self._default_templates()

        # History and rate limiting state
        self._history: List[NotificationRecord] = []
        self._rate_window_seconds: int = 60
        self._rate_max_per_window: int = 10

    # -----------------------
    # Channel configuration
    # -----------------------
    def configure_channels(self, channels_config: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Configure notification channels.

        Args:
            channels_config: Mapping of channel name to configuration dict.

        Returns:
            Summary of configuration result.
        """
        enabled = 0
        for name, cfg in channels_config.items():
            self._channels[name] = cfg or {}
            if cfg.get("enabled"):
                enabled += 1

        self.logger.info("Configured notification channels", extra={"enabled": enabled, "total": len(channels_config)})
        return {"channels_configured": list(channels_config.keys()), "enabled_count": enabled}

    def test_channel(self, channel: str) -> Dict[str, Any]:
        """Simulate a channel test.

        This does not perform any network operation; it validates presence and
        enabled status only.
        """
        cfg = self._channels.get(channel)
        if not cfg:
            return {"success": False, "error": f"Channel '{channel}' not configured"}
        if not cfg.get("enabled", False):
            return {"success": False, "error": f"Channel '{channel}' is disabled"}
        return {"success": True, "status": "reachable"}

    # -----------------------
    # Template management
    # -----------------------
    def configure_templates(self, templates: Dict[str, str], overwrite: bool = True) -> Dict[str, Any]:
        """Import templates.

        Args:
            templates: Mapping of template name to template content.
            overwrite: If False, existing templates are preserved.
        """
        imported, skipped, errors = 0, 0, []
        for name, content in templates.items():
            try:
                if name in self._templates and not overwrite:
                    skipped += 1
                    continue
                if not isinstance(content, str) or not content.strip():
                    errors.append(f"Invalid template: {name}")
                    continue
                self._templates[name] = content
                imported += 1
            except Exception as e:  # pragma: no cover
                errors.append(f"Error importing {name}: {e}")

        self.logger.info(
            "Templates configured", extra={"imported": imported, "skipped": skipped, "errors": len(errors)}
        )
        return {"templates_configured": list(templates.keys()), "imported": imported, "skipped": skipped, "errors": errors}

    def render_template(self, template_name: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Render a named template with data.

        Returns a dict with a simple title and rendered content.
        """
        template = self._templates.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        content = self._render_content(template, data)
        title = data.get("title") or f"{template_name.replace('_', ' ').title()}"
        return {"title": title, "content": content}

    # -----------------------
    # Dispatch
    # -----------------------
    def dispatch(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        priority: NotificationPriority | str = NotificationPriority.MEDIUM,
        channels: Optional[List[str]] = None,
        emergency: bool = False,
    ) -> Dict[str, Any]:
        """Dispatch a notification (simulated send).

        - Select channels (explicit list or by event-type default mapping)
        - Apply simple rate limiting per service instance
        - Record results in history
        """
        # Normalize priority from str or enum
        if isinstance(priority, NotificationPriority):
            prio = priority
        else:
            prio = NotificationPriority(str(priority).lower())
        selected_channels = channels or self._default_channels_for_event(event_type, emergency)

        # Rate limiting (simple sliding window)
        if not emergency and not self._rate_ok():
            record = self._new_record(message=f"Rate limited: {event_type}", channels=selected_channels, priority=prio)
            record.status = NotificationStatus.FAILED
            self._history.append(record)
            return {"success": False, "notification_id": record.id, "error": "rate_limited"}

        # Compose message using a matching template name if available
        template_name = self._template_name_for_event(event_type)
        message = self._render_content(self._templates.get(template_name, "{message}"), {
            **event_data,
            "message": event_data.get("message") or event_type.replace("_", " ").title(),
        })

        record = self._new_record(message=message, channels=selected_channels, priority=prio)

        # Simulate per-channel results (no real network)
        results: Dict[str, Any] = {}
        overall_success = True
        for ch in selected_channels:
            cfg = self._channels.get(ch, {})
            if not cfg.get("enabled", True):
                results[ch] = {"success": False, "error": "disabled"}
                overall_success = False
                continue
            results[ch] = {"success": True, "delivered_at": datetime.utcnow().isoformat()}

        record.results = results
        record.attempts = 1
        record.status = NotificationStatus.SENT if overall_success else NotificationStatus.FAILED
        self._history.append(record)

        return {
            "success": overall_success,
            "notification_id": record.id,
            "channels": selected_channels,
            "status": record.status,
            "results": results,
        }

    # -----------------------
    # History & Stats
    # -----------------------
    def get_history(
        self, *, limit: Optional[int] = None, status: Optional[NotificationStatus | str] = None
    ) -> List[Dict[str, Any]]:
        records = list(self._history)
        if status is not None:
            status_enum = NotificationStatus(str(status))
            records = [r for r in records if r.status == status_enum]
        records.sort(key=lambda r: r.created_at, reverse=True)
        if limit:
            records = records[:limit]
        return [self._record_to_dict(r) for r in records]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._history)
        sent = len([r for r in self._history if r.status == NotificationStatus.SENT])
        failed = len([r for r in self._history if r.status == NotificationStatus.FAILED])

        channel_stats: Dict[str, Dict[str, int]] = {}
        for r in self._history:
            for ch, res in r.results.items():
                if ch not in channel_stats:
                    channel_stats[ch] = {"total": 0, "successful": 0, "failed": 0}
                channel_stats[ch]["total"] += 1
                if res.get("success"):
                    channel_stats[ch]["successful"] += 1
                else:
                    channel_stats[ch]["failed"] += 1

        return {
            "total_notifications": total,
            "sent": sent,
            "failed": failed,
            "success_rate": (sent / total) if total else 0.0,
            "channel_statistics": channel_stats,
        }

    # -----------------------
    # Internal helpers
    # -----------------------
    def _new_record(self, *, message: str, channels: List[str], priority: NotificationPriority) -> NotificationRecord:
        nid = f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(self._history)}"
        return NotificationRecord(
            id=nid,
            message=message,
            channels=channels,
            priority=priority,
            created_at=datetime.utcnow(),
        )

    def _record_to_dict(self, r: NotificationRecord) -> Dict[str, Any]:
        return {
            "id": r.id,
            "message": r.message,
            "channels": r.channels,
            "priority": r.priority,
            "created_at": r.created_at.isoformat(),
            "status": r.status,
            "attempts": r.attempts,
            "results": r.results,
        }

    def _rate_ok(self) -> bool:
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self._rate_window_seconds)
        recent = [r for r in self._history if r.created_at > window_start]
        return len(recent) < self._rate_max_per_window

    def _default_channels_for_event(self, event_type: str, emergency: bool) -> List[str]:
        if emergency:
            # Use all enabled channels for emergencies
            return [name for name, cfg in self._channels.items() if cfg.get("enabled", True)] or ["telegram"]
        # Basic mapping; can be extended later
        mapping = {
            "signal_generated": ["telegram", "feishu"],
            "risk_alert": ["telegram", "feishu"],
            "backtest_complete": ["feishu"],
            "system_status": ["telegram"],
        }
        return mapping.get(event_type, ["telegram"])

    def _template_name_for_event(self, event_type: str) -> str:
        return {
            "signal_generated": "signal",
            "risk_alert": "risk_alert",
            "backtest_complete": "backtest_result",
            "system_status": "system",
        }.get(event_type, "system")

    def _render_content(self, template: str, data: Dict[str, Any]) -> str:
        # Prepare data with defaults and simple emoji mapping
        prepared = dict(data)
        prepared.setdefault("timestamp", datetime.utcnow().isoformat())

        # Ensure probability values <=1 remain decimals for percentage formatting
        if isinstance(prepared.get("probability"), (int, float)) and prepared["probability"] <= 1:
            prepared["probability"] = prepared["probability"]

        try:
            content = template.format(**prepared)
        except KeyError as e:
            # Render partial with missing fields noted
            missing = str(e)
            self.logger.warning("Missing template variable", extra={"missing": missing})
            content = f"Template rendering error: Missing variable {missing}"

        # Normalize whitespace (remove >2 consecutive newlines)
        content = re.sub(r"\n{3,}", "\n\n", content).strip()
        return content

    def _default_templates(self) -> Dict[str, str]:
        return {
            "signal": (
                "**New Trading Signal**\n\n"
                "Symbol: {symbol}\n"
                "Direction: {direction}\n"
                "Probability: {probability:.1%}\n"
                "Confidence: {confidence}\n"
                "Expiry: {expiry_time}\n\n"
                "Time: {timestamp}"
            ),
            "risk_alert": (
                "**RISK ALERT**\n\n"
                "Type: {alert_type}\n"
                "Symbol: {symbol}\n"
                "Message: {message}\n"
                "Time: {timestamp}"
            ),
            "backtest_result": (
                "**Backtest Completed**\n\n"
                "Strategy: {strategy_name}\n"
                "Win Rate: {win_rate:.1%}\n"
                "Trades: {total_trades}\n"
                "Max Drawdown: {max_drawdown:.2%}\n"
                "Time: {timestamp}"
            ),
            "system": (
                "**System Status**\n\n"
                "Service: {service_name}\n"
                "Status: {status}\n"
                "Time: {timestamp}"
            ),
        }
