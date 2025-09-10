import pytest

from src.services.notification_service import NotificationService, NotificationPriority, NotificationStatus


class TestNotificationService:
    def test_configure_channels_and_test(self):
        svc = NotificationService()
        result = svc.configure_channels(
            {
                "telegram": {"enabled": True},
                "feishu": {"enabled": False},
            }
        )
        assert set(result["channels_configured"]) == {"telegram", "feishu"}
        assert result["enabled_count"] == 1

        ok = svc.test_channel("telegram")
        assert ok["success"] is True

        bad = svc.test_channel("feishu")
        assert bad["success"] is False and "disabled" in bad["error"]

        missing = svc.test_channel("email")
        assert missing["success"] is False and "not configured" in missing["error"]

    def test_templates_and_render(self):
        svc = NotificationService()
        tpl = {
            "signal_generated": "Signal for {symbol} dir={direction} p={probability:.1%}"
        }
        cfg = svc.configure_templates(tpl)
        assert set(cfg["templates_configured"]) == {"signal_generated"}

        rendered = svc.render_template(
            "signal_generated",
            {"symbol": "BTCUSDT", "direction": "UP", "probability": 0.72},
        )
        assert "BTCUSDT" in rendered["content"]
        assert "72.0%" in rendered["content"]

    def test_dispatch_and_history_stats(self):
        svc = NotificationService()
        svc.configure_channels({"telegram": {"enabled": True}, "feishu": {"enabled": True}})

        resp = svc.dispatch(
            event_type="signal_generated",
            event_data={"symbol": "BTCUSDT", "direction": "UP", "probability": 0.65, "expiry_time": "10:30 UTC"},
            priority=NotificationPriority.MEDIUM,
        )
        assert resp["success"] is True
        assert resp["status"] == NotificationStatus.SENT
        assert set(resp["channels"]) == {"telegram", "feishu"}
        assert resp["notification_id"].startswith("notif_")

        hist = svc.get_history()
        assert len(hist) == 1
        assert hist[0]["status"] == NotificationStatus.SENT

        stats = svc.get_stats()
        assert stats["total_notifications"] == 1
        assert stats["sent"] == 1
        assert stats["failed"] == 0

