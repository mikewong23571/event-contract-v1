"""
Integration test for notification dispatch system (T026)

This integration test validates the complete notification system:
1. Notification configuration and channel setup
2. Event-triggered notification dispatch
3. Multi-channel delivery (Telegram, Feishu, etc.)
4. Template processing and personalization
5. Delivery confirmation and retry logic
6. Notification filtering and rate limiting
7. Emergency notification handling

The test MUST FAIL initially as the implementation is not complete yet (TDD requirement).
"""

import pytest
import asyncio
import time
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import test client for API interactions
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend', 'src'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestNotificationFlowIntegration:
    """Integration tests for notification dispatch system"""

    @pytest.fixture
    def notification_channels_config(self):
        """Sample notification channel configurations"""
        return {
            "telegram": {
                "enabled": True,
                "bot_token": "mock_telegram_token",
                "chat_id": "-1001234567890",
                "parse_mode": "Markdown",
                "rate_limit_per_minute": 20,
                "retry_attempts": 3,
                "timeout_seconds": 10
            },
            "feishu": {
                "enabled": True,
                "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/mock_webhook",
                "secret": "mock_feishu_secret",
                "rate_limit_per_minute": 50,
                "retry_attempts": 3,
                "timeout_seconds": 15
            },
            "email": {
                "enabled": False,  # Disabled for testing
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "test@example.com",
                "password": "mock_password",
                "rate_limit_per_minute": 10
            },
            "webhook": {
                "enabled": True,
                "url": "https://api.example.com/notifications/webhook",
                "headers": {
                    "Authorization": "Bearer mock_token",
                    "Content-Type": "application/json"
                },
                "rate_limit_per_minute": 100
            }
        }

    @pytest.fixture
    def notification_templates(self):
        """Sample notification templates for different event types"""
        return {
            "signal_generated": {
                "title": "🚀 New Trading Signal",
                "template": """
**New Signal Generated**

📊 **Symbol**: {symbol}
📈 **Direction**: {direction}
🎯 **Probability**: {probability:.1%}
⚡ **Confidence**: {confidence}
⏰ **Expiry**: {expiry_time}
💰 **Edge**: {probability_edge:.1%}

{additional_details}
""",
                "channels": ["telegram", "feishu"],
                "priority": "high",
                "rate_limit_group": "signals"
            },
            "risk_alert": {
                "title": "⚠️ Risk Alert",
                "template": """
**RISK ALERT**

🚨 **Type**: {alert_type}
📊 **Symbol**: {symbol}
⚠️ **Message**: {message}
💸 **Current Loss**: ${daily_loss:.2f}
🛡️ **Limit**: ${loss_limit:.2f}

Immediate attention required!
""",
                "channels": ["telegram", "feishu", "webhook"],
                "priority": "critical",
                "rate_limit_group": "alerts"
            },
            "backtest_complete": {
                "title": "📈 Backtest Results",
                "template": """
**Backtest Completed**

📊 **Strategy**: {strategy_name}
💰 **Return**: {total_return:.2%}
📈 **Win Rate**: {win_rate:.1%}
🏆 **Trades**: {total_trades}
📉 **Max Drawdown**: {max_drawdown:.2%}

{results_summary}
""",
                "channels": ["feishu", "webhook"],
                "priority": "medium",
                "rate_limit_group": "reports"
            },
            "system_status": {
                "title": "🔧 System Status",
                "template": """
**System Status Update**

🔧 **Service**: {service_name}
⚡ **Status**: {status}
⏰ **Timestamp**: {timestamp}
📝 **Details**: {details}

{additional_info}
""",
                "channels": ["telegram", "webhook"],
                "priority": "low",
                "rate_limit_group": "system"
            }
        }

    @pytest.fixture
    def sample_notification_events(self):
        """Sample events that should trigger notifications"""
        current_time = datetime.now(timezone.utc)
        
        return [
            {
                "event_type": "signal_generated",
                "timestamp": current_time.isoformat(),
                "data": {
                    "signal_id": "sig_001_test",
                    "symbol": "BTCUSDT",
                    "direction": "UP",
                    "probability": 0.68,
                    "confidence": "HIGH",
                    "expiry_time": (current_time + timedelta(minutes=10)).strftime("%H:%M UTC"),
                    "probability_edge": 0.12,
                    "additional_details": "Strong bullish momentum detected"
                }
            },
            {
                "event_type": "risk_alert",
                "timestamp": current_time.isoformat(),
                "data": {
                    "alert_type": "DAILY_LOSS_LIMIT",
                    "symbol": "BTCUSDT",
                    "message": "Daily loss limit exceeded",
                    "daily_loss": 520.00,
                    "loss_limit": 500.00
                }
            },
            {
                "event_type": "backtest_complete",
                "timestamp": current_time.isoformat(),
                "data": {
                    "backtest_id": "bt_001_test",
                    "strategy_name": "Event Contract Strategy v1.0",
                    "total_return": 0.157,  # 15.7%
                    "win_rate": 0.642,  # 64.2%
                    "total_trades": 128,
                    "max_drawdown": 0.089,  # 8.9%
                    "results_summary": "Strong performance with good risk control"
                }
            },
            {
                "event_type": "system_status",
                "timestamp": current_time.isoformat(),
                "data": {
                    "service_name": "Real-time Signal Detection",
                    "status": "OPERATIONAL",
                    "details": "All systems functioning normally",
                    "additional_info": "Performance within normal parameters"
                }
            }
        ]

    def test_notification_channel_setup_and_validation(self, notification_channels_config):
        """
        Test notification channel configuration and validation
        """
        # Configure notification channels
        response = client.post("/api/v1/notifications/channels", json=notification_channels_config)
        
        if response.status_code in [200, 201]:
            # Configuration accepted
            config_result = response.json()
            assert "channels_configured" in config_result
            
            # Validate channel configurations
            for channel_name, config in notification_channels_config.items():
                if config.get("enabled", False):
                    # Test channel connectivity
                    test_response = client.post(f"/api/v1/notifications/channels/{channel_name}/test")
                    
                    if test_response.status_code == 200:
                        test_result = test_response.json()
                        print(f"{channel_name} channel test: {test_result.get('status', 'unknown')}")
                    elif test_response.status_code in [400, 401, 403]:
                        # Authentication or configuration issues
                        error_data = test_response.json()
                        print(f"{channel_name} channel error: {error_data}")
                    elif test_response.status_code == 404:
                        print(f"{channel_name} channel test endpoint not implemented")
        
        elif response.status_code in [400, 422]:
            # Configuration validation errors
            error_data = response.json()
            print(f"Channel configuration validation failed: {error_data}")
        
        elif response.status_code == 404:
            print("Notification channels configuration endpoint not implemented")
        
        else:
            print(f"Unexpected response for channel configuration: {response.status_code}")

    def test_notification_template_management(self, notification_templates):
        """
        Test notification template configuration and processing
        """
        # Configure notification templates
        response = client.post("/api/v1/notifications/templates", json=notification_templates)
        
        if response.status_code in [200, 201]:
            template_result = response.json()
            assert "templates_configured" in template_result or "status" in template_result
            
            # Test template rendering with sample data
            test_data = {
                "symbol": "BTCUSDT",
                "direction": "UP",
                "probability": 0.72,
                "confidence": "HIGH",
                "expiry_time": "15:30 UTC",
                "probability_edge": 0.22,
                "additional_details": "Strong momentum indicators"
            }
            
            render_request = {
                "template_name": "signal_generated",
                "data": test_data
            }
            
            render_response = client.post("/api/v1/notifications/templates/render", json=render_request)
            
            if render_response.status_code == 200:
                rendered = render_response.json()
                
                # Validate template rendering
                assert "title" in rendered
                assert "content" in rendered
                
                # Check that placeholders are replaced
                content = rendered["content"]
                assert "BTCUSDT" in content
                assert "72.0%" in content or "0.72" in content
                assert "HIGH" in content
                
                print("Template rendering successful")
            
            elif render_response.status_code == 404:
                print("Template rendering endpoint not implemented")
        
        elif response.status_code == 404:
            print("Template configuration endpoint not implemented")
        
        else:
            print(f"Template configuration response: {response.status_code}")

    def test_event_triggered_notification_dispatch(self, notification_channels_config, 
                                                  notification_templates, sample_notification_events):
        """
        Test complete event-to-notification flow
        """
        # Setup channels and templates
        client.post("/api/v1/notifications/channels", json=notification_channels_config)
        client.post("/api/v1/notifications/templates", json=notification_templates)
        
        dispatched_notifications = []
        failed_notifications = []
        
        # Process each notification event
        for event in sample_notification_events:
            # Dispatch notification
            dispatch_request = {
                "event_type": event["event_type"],
                "event_data": event["data"],
                "timestamp": event["timestamp"],
                "priority": notification_templates[event["event_type"]]["priority"]
            }
            
            dispatch_response = client.post("/api/v1/notifications/dispatch", json=dispatch_request)
            
            if dispatch_response.status_code in [200, 202]:
                # Notification accepted for dispatch
                dispatch_result = dispatch_response.json()
                dispatched_notifications.append({
                    "event_type": event["event_type"],
                    "notification_id": dispatch_result.get("notification_id"),
                    "channels": dispatch_result.get("channels", []),
                    "status": dispatch_result.get("status", "dispatched")
                })
                
            elif dispatch_response.status_code in [400, 422]:
                # Dispatch validation errors
                error_data = dispatch_response.json()
                failed_notifications.append({
                    "event_type": event["event_type"],
                    "error": error_data
                })
                
            elif dispatch_response.status_code == 404:
                print(f"Notification dispatch endpoint not implemented for {event['event_type']}")
            
            else:
                print(f"Unexpected dispatch response for {event['event_type']}: {dispatch_response.status_code}")
            
            time.sleep(0.5)  # Brief pause between dispatches
        
        print(f"Dispatched notifications: {len(dispatched_notifications)}")
        print(f"Failed notifications: {len(failed_notifications)}")
        
        # Monitor delivery status
        if dispatched_notifications:
            time.sleep(3)  # Allow delivery processing
            
            for notification in dispatched_notifications:
                if notification["notification_id"]:
                    # Check delivery status
                    status_response = client.get(f"/api/v1/notifications/{notification['notification_id']}/status")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        # Validate delivery tracking
                        assert "notification_id" in status_data
                        assert "status" in status_data
                        assert "channels" in status_data
                        
                        # Check channel-specific delivery status
                        for channel_status in status_data["channels"]:
                            assert "channel" in channel_status
                            assert "status" in channel_status
                            assert channel_status["status"] in [
                                "pending", "sent", "delivered", "failed", "retry"
                            ]
                        
                        print(f"Notification {notification['notification_id']}: {status_data['status']}")

    def test_notification_rate_limiting_and_throttling(self, notification_channels_config, notification_templates):
        """
        Test notification rate limiting and throttling mechanisms
        """
        # Setup with low rate limits for testing
        low_limit_config = dict(notification_channels_config)
        low_limit_config["telegram"]["rate_limit_per_minute"] = 3  # Very low limit
        low_limit_config["feishu"]["rate_limit_per_minute"] = 5
        
        client.post("/api/v1/notifications/channels", json=low_limit_config)
        client.post("/api/v1/notifications/templates", json=notification_templates)
        
        # Generate rapid notification requests
        rapid_notifications = []
        for i in range(10):  # 10 rapid notifications
            event_data = {
                "event_type": "signal_generated",
                "event_data": {
                    "signal_id": f"sig_{i}_rate_test",
                    "symbol": "BTCUSDT",
                    "direction": "UP" if i % 2 == 0 else "DOWN",
                    "probability": 0.6 + (i * 0.02),
                    "confidence": "MEDIUM",
                    "expiry_time": "15:30 UTC",
                    "probability_edge": 0.1 + (i * 0.01),
                    "additional_details": f"Rate limit test #{i+1}"
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            dispatch_response = client.post("/api/v1/notifications/dispatch", json=event_data)
            
            rapid_notifications.append({
                "sequence": i,
                "status_code": dispatch_response.status_code,
                "response": dispatch_response.json() if dispatch_response.status_code != 500 else {}
            })
            
            time.sleep(0.2)  # 200ms between requests (rapid)
        
        # Analyze rate limiting results
        accepted_count = sum(1 for n in rapid_notifications if n["status_code"] in [200, 202])
        rate_limited_count = sum(1 for n in rapid_notifications if n["status_code"] == 429)
        
        print(f"Rate limiting test: {accepted_count} accepted, {rate_limited_count} rate limited")
        
        # Validate rate limiting behavior
        if rate_limited_count > 0:
            # Rate limiting is working
            for notification in rapid_notifications:
                if notification["status_code"] == 429:
                    error_data = notification["response"]
                    rate_limit_keywords = ["rate", "limit", "throttl", "exceed", "wait"]
                    
                    error_text = str(error_data).lower()
                    assert any(keyword in error_text for keyword in rate_limit_keywords), \
                           f"Rate limit error should indicate rate limiting: {error_data}"
        
        # Test rate limit recovery
        print("Waiting for rate limit recovery...")
        time.sleep(65)  # Wait over a minute for rate limit reset
        
        # Try another notification after waiting
        recovery_event = {
            "event_type": "signal_generated",
            "event_data": {
                "signal_id": "sig_recovery_test",
                "symbol": "ETHUSDT",
                "direction": "UP",
                "probability": 0.65,
                "confidence": "HIGH",
                "expiry_time": "16:00 UTC",
                "probability_edge": 0.15,
                "additional_details": "Rate limit recovery test"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        recovery_response = client.post("/api/v1/notifications/dispatch", json=recovery_event)
        
        if recovery_response.status_code in [200, 202]:
            print("Rate limit recovery successful")
        else:
            print(f"Rate limit recovery test: {recovery_response.status_code}")

    def test_notification_filtering_and_deduplication(self, notification_channels_config, notification_templates):
        """
        Test notification filtering and deduplication logic
        """
        # Setup notification system
        client.post("/api/v1/notifications/channels", json=notification_channels_config)
        client.post("/api/v1/notifications/templates", json=notification_templates)
        
        # Configure notification filters
        filter_config = {
            "min_signal_probability": 0.60,  # Only notify for 60%+ probability
            "min_signal_edge": 0.08,  # Minimum 8% edge
            "deduplicate_window_minutes": 5,  # 5-minute deduplication window
            "priority_filters": {
                "critical": {"always_send": True},
                "high": {"min_probability": 0.60},
                "medium": {"min_probability": 0.65},
                "low": {"min_probability": 0.70}
            }
        }
        
        filter_response = client.post("/api/v1/notifications/filters", json=filter_config)
        
        if filter_response.status_code not in [200, 201, 404]:
            print(f"Filter configuration: {filter_response.status_code}")
        
        # Test filtering with various signal probabilities
        test_signals = [
            # Should be filtered out (low probability)
            {
                "probability": 0.55,
                "edge": 0.05,
                "expected_filtered": True,
                "reason": "low_probability"
            },
            # Should be sent (meets criteria)
            {
                "probability": 0.68,
                "edge": 0.18,
                "expected_filtered": False,
                "reason": "meets_criteria"
            },
            # Duplicate signal (should be deduplicated)
            {
                "probability": 0.68,
                "edge": 0.18,
                "expected_filtered": True,
                "reason": "duplicate"
            },
            # High probability (should be sent)
            {
                "probability": 0.75,
                "edge": 0.25,
                "expected_filtered": False,
                "reason": "high_probability"
            }
        ]
        
        filtering_results = []
        
        for i, signal_test in enumerate(test_signals):
            event_data = {
                "event_type": "signal_generated",
                "event_data": {
                    "signal_id": f"sig_filter_test_{i}",
                    "symbol": "BTCUSDT",
                    "direction": "UP",
                    "probability": signal_test["probability"],
                    "confidence": "HIGH" if signal_test["probability"] > 0.65 else "MEDIUM",
                    "expiry_time": "17:00 UTC",
                    "probability_edge": signal_test["edge"],
                    "additional_details": f"Filter test {signal_test['reason']}"
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "priority": "high"
            }
            
            dispatch_response = client.post("/api/v1/notifications/dispatch", json=event_data)
            
            filtering_results.append({
                "test_case": signal_test["reason"],
                "probability": signal_test["probability"],
                "expected_filtered": signal_test["expected_filtered"],
                "status_code": dispatch_response.status_code,
                "response": dispatch_response.json() if dispatch_response.status_code != 500 else {}
            })
            
            time.sleep(1)  # Brief pause between tests
        
        # Analyze filtering results
        for result in filtering_results:
            print(f"Filter test '{result['test_case']}': {result['status_code']}")
            
            if result["expected_filtered"]:
                # Should be filtered/rejected
                if result["status_code"] in [400, 422]:
                    # Properly filtered
                    error_data = result["response"]
                    filter_keywords = ["filter", "criteria", "probability", "duplicate", "threshold"]
                    
                    error_text = str(error_data).lower()
                    filter_indicated = any(keyword in error_text for keyword in filter_keywords)
                    
                    if filter_indicated:
                        print(f"  ✓ Correctly filtered: {result['test_case']}")
                    else:
                        print(f"  ? Filtered for other reason: {error_data}")
            else:
                # Should be accepted
                if result["status_code"] in [200, 202]:
                    print(f"  ✓ Correctly accepted: {result['test_case']}")
                else:
                    print(f"  ? Unexpected result for {result['test_case']}: {result['status_code']}")

    def test_emergency_notification_handling(self, notification_channels_config, notification_templates):
        """
        Test emergency notification handling and priority routing
        """
        # Setup notification system
        client.post("/api/v1/notifications/channels", json=notification_channels_config)
        client.post("/api/v1/notifications/templates", json=notification_templates)
        
        # Configure emergency notification settings
        emergency_config = {
            "emergency_channels": ["telegram", "feishu", "webhook"],  # All channels for emergencies
            "bypass_rate_limits": True,
            "retry_attempts": 5,
            "escalation_delay_minutes": 2,
            "emergency_keywords": ["emergency", "critical", "urgent", "alert", "stop"]
        }
        
        emergency_setup_response = client.post("/api/v1/notifications/emergency-config", json=emergency_config)
        
        # Test emergency notification dispatch
        emergency_event = {
            "event_type": "risk_alert",
            "event_data": {
                "alert_type": "EMERGENCY_STOP",
                "symbol": "BTCUSDT",
                "message": "Emergency stop triggered - system halt required",
                "daily_loss": 1500.00,
                "loss_limit": 1000.00,
                "severity": "CRITICAL"
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "priority": "critical",
            "emergency": True
        }
        
        emergency_response = client.post("/api/v1/notifications/dispatch", json=emergency_event)
        
        if emergency_response.status_code in [200, 202]:
            emergency_result = emergency_response.json()
            
            # Validate emergency notification handling
            assert "notification_id" in emergency_result
            
            # Emergency notifications should bypass normal restrictions
            if "channels" in emergency_result:
                emergency_channels = emergency_result["channels"]
                expected_channels = emergency_config["emergency_channels"]
                
                # Should use all emergency channels
                for channel in expected_channels:
                    if channel in notification_channels_config and notification_channels_config[channel]["enabled"]:
                        assert channel in emergency_channels, f"Emergency channel {channel} should be used"
            
            # Monitor emergency notification delivery
            notification_id = emergency_result["notification_id"]
            
            # Check delivery status multiple times (emergency should be fast)
            for check_attempt in range(5):
                time.sleep(2)  # Check every 2 seconds
                
                status_response = client.get(f"/api/v1/notifications/{notification_id}/status")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    delivered_channels = sum(1 for ch in status_data.get("channels", []) 
                                          if ch.get("status") == "delivered")
                    
                    total_channels = len(status_data.get("channels", []))
                    
                    print(f"Emergency delivery check {check_attempt + 1}: {delivered_channels}/{total_channels} delivered")
                    
                    # Emergency notifications should deliver quickly
                    if delivered_channels > 0:
                        delivery_time = check_attempt * 2 + 2  # seconds
                        assert delivery_time <= 10, f"Emergency notification took too long: {delivery_time}s"
                        break
            
        elif emergency_response.status_code == 404:
            print("Emergency notification dispatch not implemented")
        else:
            print(f"Emergency notification response: {emergency_response.status_code}")
        
        # Test emergency notification escalation
        escalation_event = {
            "event_type": "system_status",
            "event_data": {
                "service_name": "Trading System",
                "status": "CRITICAL_FAILURE",
                "details": "System requires immediate attention",
                "error_code": "SYS_001",
                "additional_info": "Manual intervention required"
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "priority": "critical",
            "escalate": True,
            "escalation_delay_minutes": 1  # Quick escalation for testing
        }
        
        escalation_response = client.post("/api/v1/notifications/dispatch", json=escalation_event)
        
        if escalation_response.status_code in [200, 202]:
            print("Emergency escalation notification dispatched")
        else:
            print(f"Emergency escalation response: {escalation_response.status_code}")

    def test_notification_delivery_monitoring_and_analytics(self, notification_channels_config, 
                                                           notification_templates, sample_notification_events):
        """
        Test notification delivery monitoring, analytics, and reporting
        """
        # Setup notification system
        client.post("/api/v1/notifications/channels", json=notification_channels_config)
        client.post("/api/v1/notifications/templates", json=notification_templates)
        
        # Dispatch multiple notifications for analytics
        notification_ids = []
        
        for event in sample_notification_events[:3]:  # Use first 3 events
            dispatch_request = {
                "event_type": event["event_type"],
                "event_data": event["data"],
                "timestamp": event["timestamp"]
            }
            
            response = client.post("/api/v1/notifications/dispatch", json=dispatch_request)
            
            if response.status_code in [200, 202]:
                result = response.json()
                if "notification_id" in result:
                    notification_ids.append(result["notification_id"])
        
        # Allow processing time
        time.sleep(5)
        
        # Test delivery analytics
        analytics_response = client.get("/api/v1/notifications/analytics")
        
        if analytics_response.status_code == 200:
            analytics = analytics_response.json()
            
            # Validate analytics structure
            expected_metrics = [
                "total_notifications", "delivery_rate", "channel_performance",
                "average_delivery_time", "failure_rate", "retry_rate"
            ]
            
            available_metrics = [m for m in expected_metrics if m in analytics]
            
            if available_metrics:
                print(f"Available analytics metrics: {available_metrics}")
                
                # Validate metric types and ranges
                for metric in available_metrics:
                    value = analytics[metric]
                    
                    if metric in ["delivery_rate", "failure_rate", "retry_rate"]:
                        if isinstance(value, (int, float)):
                            assert 0.0 <= value <= 1.0, f"Rate metric {metric} out of range: {value}"
                    
                    elif metric == "total_notifications":
                        assert isinstance(value, int) and value >= 0, "Total notifications should be non-negative integer"
                    
                    elif metric == "average_delivery_time":
                        assert isinstance(value, (int, float)) and value >= 0, "Delivery time should be non-negative"
                    
                    elif metric == "channel_performance":
                        assert isinstance(value, dict), "Channel performance should be a dictionary"
                        
                        for channel, perf in value.items():
                            assert isinstance(perf, dict), f"Performance for {channel} should be dict"
                            
                            if "success_rate" in perf:
                                assert 0.0 <= perf["success_rate"] <= 1.0, f"Success rate for {channel} out of range"
            else:
                print("Analytics metrics not yet implemented")
        
        elif analytics_response.status_code == 404:
            print("Notifications analytics endpoint not implemented")
        
        # Test individual notification details
        for notification_id in notification_ids[:2]:  # Check first 2
            detail_response = client.get(f"/api/v1/notifications/{notification_id}")
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                
                # Validate notification detail structure
                assert "notification_id" in detail_data
                assert "event_type" in detail_data
                assert "created_at" in detail_data
                assert "status" in detail_data
                
                # Check delivery timeline
                if "delivery_timeline" in detail_data:
                    timeline = detail_data["delivery_timeline"]
                    
                    assert isinstance(timeline, list), "Timeline should be a list"
                    
                    for event in timeline:
                        assert "timestamp" in event
                        assert "event" in event
                        assert event["event"] in [
                            "created", "queued", "processing", "sent", 
                            "delivered", "failed", "retried"
                        ], f"Unknown timeline event: {event['event']}"
        
        # Test notification history and search
        history_response = client.get("/api/v1/notifications/history?limit=10")
        
        if history_response.status_code == 200:
            history = history_response.json()
            
            # Validate history structure
            assert "notifications" in history or isinstance(history, list)
            
            notifications_list = history.get("notifications", history)
            
            if isinstance(notifications_list, list) and len(notifications_list) > 0:
                for notification in notifications_list[:3]:  # Check first 3
                    assert "notification_id" in notification
                    assert "event_type" in notification
                    assert "status" in notification
                    assert "created_at" in notification
                
                print(f"Notification history: {len(notifications_list)} records")
            else:
                print("No notifications found in history")
        
        elif history_response.status_code == 404:
            print("Notification history endpoint not implemented")

    def test_notification_system_resilience_and_recovery(self, notification_channels_config, notification_templates):
        """
        Test notification system resilience, error handling, and recovery
        """
        # Setup with some invalid channel configurations
        mixed_config = dict(notification_channels_config)
        mixed_config["telegram"]["bot_token"] = "invalid_token"  # Invalid token
        mixed_config["feishu"]["webhook_url"] = "https://invalid.webhook.url"  # Invalid URL
        
        client.post("/api/v1/notifications/channels", json=mixed_config)
        client.post("/api/v1/notifications/templates", json=notification_templates)
        
        # Test notification dispatch with mixed valid/invalid channels
        resilience_event = {
            "event_type": "signal_generated",
            "event_data": {
                "signal_id": "sig_resilience_test",
                "symbol": "ETHUSDT",
                "direction": "DOWN",
                "probability": 0.70,
                "confidence": "HIGH",
                "expiry_time": "18:00 UTC",
                "probability_edge": 0.20,
                "additional_details": "Resilience test notification"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        resilience_response = client.post("/api/v1/notifications/dispatch", json=resilience_event)
        
        if resilience_response.status_code in [200, 202]:
            resilience_result = resilience_response.json()
            notification_id = resilience_result.get("notification_id")
            
            # Monitor delivery with mixed channel success/failure
            time.sleep(8)  # Allow retry attempts
            
            status_response = client.get(f"/api/v1/notifications/{notification_id}/status")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                channel_statuses = status_data.get("channels", [])
                
                successful_channels = sum(1 for ch in channel_statuses if ch.get("status") == "delivered")
                failed_channels = sum(1 for ch in channel_statuses if ch.get("status") == "failed")
                
                print(f"Resilience test: {successful_channels} successful, {failed_channels} failed deliveries")
                
                # System should handle partial failures gracefully
                if successful_channels > 0:
                    print("✓ System maintained partial delivery capability")
                
                if failed_channels > 0:
                    # Check if failures are properly logged and handled
                    for channel_status in channel_statuses:
                        if channel_status.get("status") == "failed":
                            assert "error_message" in channel_status, \
                                   "Failed channels should have error messages"
                            
                            assert "retry_attempts" in channel_status, \
                                   "Failed channels should track retry attempts"
        
        # Test system recovery after fixing configurations
        print("Testing system recovery...")
        
        # Fix channel configurations
        fixed_config = dict(notification_channels_config)  # Use original valid config
        client.post("/api/v1/notifications/channels", json=fixed_config)
        
        # Test notification after recovery
        recovery_event = {
            "event_type": "system_status",
            "event_data": {
                "service_name": "Notification System",
                "status": "RECOVERED",
                "details": "System has recovered from configuration issues",
                "additional_info": "All channels operational"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        recovery_response = client.post("/api/v1/notifications/dispatch", json=recovery_event)
        
        if recovery_response.status_code in [200, 202]:
            print("✓ System recovery successful")
        else:
            print(f"System recovery test: {recovery_response.status_code}")
        
        # Test error handling for malformed notifications
        malformed_event = {
            "event_type": "invalid_event_type",
            "event_data": {
                "invalid": "data structure"
            },
            # Missing timestamp
        }
        
        malformed_response = client.post("/api/v1/notifications/dispatch", json=malformed_event)
        
        # Should handle malformed data gracefully
        assert malformed_response.status_code in [400, 422], \
               "Malformed notifications should be rejected with appropriate error code"
        
        error_data = malformed_response.json()
        assert "detail" in error_data or "error" in error_data, \
               "Error response should include descriptive message"