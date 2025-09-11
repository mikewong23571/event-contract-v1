#!/usr/bin/env python3
"""Notification CLI

Minimal, structured CLI for sending and validating notifications with
constitutional flags and JSON/text output.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any, Dict, List

try:
    from importlib.metadata import version as _pkg_version
except Exception:  # pragma: no cover
    _pkg_version = None  # type: ignore

from ..lib.notification_manager.notification_manager import (
    NotificationManager,
    NotificationPriority,
)
from ..lib.notification_manager.telegram_notifier import TelegramNotifier
from ..lib.notification_manager.feishu_notifier import FeishuNotifier


PACKAGE_NAME = "event-contract-notifications"
DEFAULT_VERSION = "0.1.0"


def _get_version() -> str:
    try:
        if _pkg_version is not None:
            return _pkg_version(PACKAGE_NAME)
    except Exception:
        pass
    return DEFAULT_VERSION


def _print(data: Any, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(data, indent=2, default=str))
    else:
        if isinstance(data, str):
            print(data)
        else:
            print(json.dumps(data, indent=2, default=str))


def _load_config(path: str | None) -> Dict[str, Any]:
    if not path:
        # Basic sample config placeholder – real credentials should be provided via file
        return {
            "telegram": {"bot_token": "", "default_chat_id": ""},
            "feishu": {"webhook_url": "", "secret": ""},
            "signal_channels": ["telegram"],
        }
    with open(path, "r") as f:
        return json.load(f)


async def cmd_send(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config_file)
    mgr = NotificationManager(cfg)
    priority = getattr(NotificationPriority, args.priority.upper(), NotificationPriority.MEDIUM)
    channels = [c.strip() for c in args.channels.split(",")]
    res = await mgr.send_notification(args.message, channels, priority)
    _print(res, args.format)
    return 0


async def cmd_validate(args: argparse.Namespace) -> int:
    cfg = _load_config(args.config_file)
    out: Dict[str, Any] = {}
    if "telegram" in cfg:
        tel = TelegramNotifier(cfg["telegram"])  # type: ignore[index]
        out["telegram"] = {"config": tel.validate_config()}
    if "feishu" in cfg:
        fs = FeishuNotifier(cfg["feishu"])  # type: ignore[index]
        out["feishu"] = {"config": fs.validate_config()}
    _print(out, args.format)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Notification CLI Tool")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )
    parser.add_argument("--config-file", help="Path to notification configuration JSON")
    sub = parser.add_subparsers(dest="command")

    p_send = sub.add_parser("send", help="Send a simple message")
    p_send.add_argument("--message", required=True)
    p_send.add_argument("--channels", default="telegram")
    p_send.add_argument(
        "--priority",
        default="medium",
        choices=["low", "medium", "high", "urgent"],
    )
    p_send.set_defaults(func=cmd_send)

    p_val = sub.add_parser("validate", help="Validate channel configuration")
    p_val.set_defaults(func=cmd_validate)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "version", False):
        print(_get_version())
        return 0

    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    try:
        if asyncio.iscoroutinefunction(args.func):  # type: ignore[attr-defined]
            return int(asyncio.run(args.func(args)))  # type: ignore[attr-defined]
        return int(args.func(args))  # type: ignore[attr-defined]
    except KeyboardInterrupt:  # pragma: no cover
        return 130


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

