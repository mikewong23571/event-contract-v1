"""Notification channel clients.

Provides concrete clients for external notification channels such as
Telegram and Feishu. These clients focus on a small, well-typed surface
area used by the notification dispatcher and services.
"""

__all__ = [
    "telegram_client",
    "feishu_client",
]

