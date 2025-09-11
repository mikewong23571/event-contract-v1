#!/usr/bin/env python3
"""Signal Generation CLI

This CLI exposes core signal generation capabilities for quick, scriptable use.

Constitutional CLI requirements:
- Supports --help, --version, and --format (json|text)
- Emits machine-readable JSON to stdout when --format json
- Emits human-readable output when --format text

Implements minimal, focused commands that delegate to the library-first
implementations in `backend/src/lib/signal_generation` without re-creating
business logic.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List

from ..models.market_data import MarketData
from ..lib.signal_generation.signal_generator import SignalGenerator
from ._utils import get_version, print_output


PACKAGE_NAME = "event-contract-backend"
DEFAULT_VERSION = "0.1.0"


def _create_sample_market_data(symbol: str, count: int = 30) -> List[MarketData]:
    base_price = Decimal("50000.00")
    data: List[MarketData] = []
    for i in range(count):
        timestamp = datetime.utcnow() - timedelta(minutes=(count - i))
        price_variation = Decimal(str(float(base_price) * (1 + (i % 10 - 5) * 0.002)))
        data.append(
            MarketData(
                symbol=symbol,
                timestamp=timestamp,
                open_price=price_variation,
                high_price=price_variation * Decimal("1.01"),
                low_price=price_variation * Decimal("0.99"),
                close_price=price_variation * Decimal("1.005"),
                volume=Decimal("100.0"),
                quote_volume=Decimal("5000.0"),
                trade_count=50,
                source="sample",
            )
        )
    return data


def cmd_generate(args: argparse.Namespace) -> int:
    generator = SignalGenerator(strategy_version=args.strategy_version)
    if args.sample_data:
        market_data = _create_sample_market_data(args.symbol, args.data_points)
    else:
        print_output("Error: Real market data fetching not implemented in this CLI", args.format)
        return 2

    signal = generator.generate_signal(
        market_data=market_data, symbol=args.symbol, expiry_minutes=args.expiry_minutes
    )
    if not signal:
        print_output("No signal generated", args.format)
        return 1

    payload: Dict[str, Any] = signal.dict()
    if args.format == "text":
        lines = [
            f"Symbol: {payload['symbol']}",
            f"Direction: {payload['direction']}",
            f"Probability: {payload['predicted_probability']}",
            f"Confidence: {payload['confidence_level']}",
            f"Expiry: {payload['expiry_time']}",
        ]
        print_output("\n".join(lines), args.format)
    else:
        print_output(payload, args.format)
    return 0


def cmd_batch(args: argparse.Namespace) -> int:
    generator = SignalGenerator(strategy_version=args.strategy_version)
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    market_data_dict: Dict[str, List[MarketData]] = {
        sym: _create_sample_market_data(sym, args.data_points) for sym in symbols
    }
    signals = generator.batch_generate_signals(
        market_data_dict=market_data_dict, expiry_minutes=args.expiry_minutes
    )
    payload = [
        {
            "symbol": s.symbol,
            "direction": s.direction,
            "probability": s.predicted_probability,
            "confidence": s.confidence_level,
            "expiry": s.expiry_time,
        }
        for s in signals
    ]
    print_output({"count": len(payload), "signals": payload}, args.format)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        data = json.loads(args.signal_json)
    except Exception as e:  # pragma: no cover - exercised via CLI
        print_output(f"Error parsing signal JSON: {e}", args.format)
        return 2
    # Basic presence checks to avoid over-scoping
    required = ["symbol", "direction", "predicted_probability", "expiry_time"]
    missing = [k for k in required if k not in data]
    result = {
        "valid": len(missing) == 0,
        "missing_fields": missing,
    }
    print_output(result, args.format)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Signal Generation CLI Tool")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--strategy-version", default="v1.0", help="Strategy/algorithm version"
    )

    sub = parser.add_subparsers(dest="command")

    p_gen = sub.add_parser("generate", help="Generate a single trading signal")
    p_gen.add_argument("--symbol", required=True, help="Symbol, e.g. BTCUSDT")
    p_gen.add_argument("--expiry-minutes", type=int, default=15)
    p_gen.add_argument("--sample-data", action="store_true", help="Use sample data")
    p_gen.add_argument("--data-points", type=int, default=30)
    p_gen.set_defaults(func=cmd_generate)

    p_batch = sub.add_parser("batch", help="Generate signals for multiple symbols")
    p_batch.add_argument("--symbols", required=True, help="Comma-separated symbols")
    p_batch.add_argument("--expiry-minutes", type=int, default=15)
    p_batch.add_argument("--data-points", type=int, default=30)
    p_batch.set_defaults(func=cmd_batch)

    p_val = sub.add_parser("validate", help="Validate a signal JSON payload")
    p_val.add_argument("--signal-json", required=True, help="Signal JSON string")
    p_val.set_defaults(func=cmd_validate)

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
