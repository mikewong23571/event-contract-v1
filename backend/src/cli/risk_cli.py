#!/usr/bin/env python3
"""Risk Management CLI

Exposes core risk operations with JSON/text output and version flag.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from ..lib.risk_management.risk_manager import RiskManager
from ..lib.risk_management.position_validator import PositionValidator
from ..lib.risk_management.exposure_calculator import ExposureCalculator
from ..models.risk_parameters import RiskParameters
from ..models.trading_signal import TradingSignal
from ._utils import get_version, print_output


PACKAGE_NAME = "event-contract-backend"
DEFAULT_VERSION = "0.1.0"


def _sample_risk_params(user_id: str = "test_user") -> RiskParameters:
    return RiskParameters(
        user_id=user_id,
        max_bet_size=Decimal("100.00"),
        max_daily_bets=10,
        max_parallel_positions=5,
        min_probability_edge=Decimal("0.05"),
        frequency_limit_minutes=15,
        max_daily_loss=Decimal("500.00"),
    )


def cmd_validate(args: argparse.Namespace) -> int:
    rm = RiskManager()
    rp = _sample_risk_params(args.user_id)
    sig = TradingSignal(
        timestamp=datetime.utcnow(),
        symbol=args.symbol,
        direction=args.direction,
        predicted_probability=args.probability,
        confidence_level="MEDIUM",
        expiry_time=datetime.utcnow() + timedelta(minutes=15),
        strategy_version="v1.0",
        technical_indicators={},
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    positions: List[Dict[str, Any]] = []
    daily_stats = {
        "bet_count": args.daily_bets,
        "total_pnl": Decimal(str(args.daily_pnl)),
        "last_signal_time": datetime.utcnow() - timedelta(minutes=args.last_signal_minutes),
    }
    valid, message = rm.validate_signal_risk(sig, rp, positions, daily_stats)
    print_output({"valid": valid, "message": message}, args.format)
    return 0


def cmd_position_size(args: argparse.Namespace) -> int:
    rm = RiskManager()
    rp = _sample_risk_params(args.user_id)
    sig = TradingSignal(
        timestamp=datetime.utcnow(),
        symbol=args.symbol,
        direction="UP",
        predicted_probability=args.probability,
        confidence_level="MEDIUM",
        expiry_time=datetime.utcnow() + timedelta(minutes=15),
        strategy_version="v1.0",
        technical_indicators={},
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    size = rm.calculate_position_size(sig, rp, Decimal(str(args.account_balance)))
    print_output({"recommended_position_size": float(size)}, args.format)
    return 0


def cmd_exposure(args: argparse.Namespace) -> int:
    calc = ExposureCalculator()
    positions = args.positions or []
    report = calc.generate_exposure_report(positions)
    print_output(report, args.format)
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    validator = PositionValidator()
    position = {
        "id": "pos-1",
        "symbol": args.symbol,
        "direction": args.direction,
        "size": args.size,
        "entry_price": args.entry_price,
        "status": "active",
        "entry_time": datetime.utcnow() - timedelta(minutes=args.age_minutes),
    }
    rp = _sample_risk_params()
    health = validator.check_position_health(position, Decimal(str(args.current_price)), rp)
    print_output({"position": position, "health": health}, args.format)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Risk Management CLI Tool")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )
    parser.add_argument("--user-id", default="test_user")
    sub = parser.add_subparsers(dest="command")

    p_val = sub.add_parser("validate", help="Validate a signal against risk params")
    p_val.add_argument("--symbol", required=True)
    p_val.add_argument("--direction", required=True, choices=["UP", "DOWN"])
    p_val.add_argument("--probability", type=float, required=True)
    p_val.add_argument("--daily-bets", type=int, default=0)
    p_val.add_argument("--daily-pnl", type=float, default=0)
    p_val.add_argument("--last-signal-minutes", type=int, default=20)
    p_val.set_defaults(func=cmd_validate)

    p_size = sub.add_parser("position-size", help="Calculate recommended position size")
    p_size.add_argument("--symbol", required=True)
    p_size.add_argument("--probability", type=float, required=True)
    p_size.add_argument("--account-balance", type=float, default=1000)
    p_size.set_defaults(func=cmd_position_size)

    p_exp = sub.add_parser("exposure", help="Generate exposure report from positions JSON")
    p_exp.add_argument("--positions", type=json.loads, help="Positions JSON array")
    p_exp.set_defaults(func=cmd_exposure)

    p_health = sub.add_parser("health", help="Check a single position health")
    p_health.add_argument("--symbol", required=True)
    p_health.add_argument("--direction", required=True, choices=["UP", "DOWN"])
    p_health.add_argument("--size", type=float, required=True)
    p_health.add_argument("--entry-price", type=float, required=True)
    p_health.add_argument("--current-price", type=float, required=True)
    p_health.add_argument("--age-minutes", type=int, default=30)
    p_health.set_defaults(func=cmd_health)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "version", False):
        print(get_version(PACKAGE_NAME, DEFAULT_VERSION))
        return 0

    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    try:
        return int(args.func(args))  # type: ignore[attr-defined]
    except KeyboardInterrupt:  # pragma: no cover
        return 130


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
