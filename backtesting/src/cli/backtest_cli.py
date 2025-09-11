#!/usr/bin/env python3
"""Backtesting CLI

Thin wrapper that surfaces essential backtesting commands with version and
format flags, delegating to the library implementation.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

try:
    from importlib.metadata import version as _pkg_version
except Exception:  # pragma: no cover
    _pkg_version = None  # type: ignore

import pandas as pd

from ..lib.backtesting_engine.backtesting_engine import BacktestingEngine
from ..lib.backtesting_engine.strategy_simulator import StrategySimulator
from ..lib.backtesting_engine.report_generator import ReportGenerator
from ..lib.backtesting_engine.cli import create_sample_market_data
from ..config.logging import configure_structlog


PACKAGE_NAME = "event-contract-backtesting"
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


def cmd_backtest(args: argparse.Namespace) -> int:
    if args.data_file:
        try:
            market_data: pd.DataFrame = pd.read_csv(args.data_file, index_col=0, parse_dates=True)
        except Exception as e:
            _print({"error": f"Failed to load data: {e}"}, args.format)
            return 2
    else:
        market_data = create_sample_market_data(args.symbol, args.days)

    params: Dict[str, Any] = {}
    if args.parameters:
        try:
            params = json.loads(args.parameters)
        except Exception as e:
            _print({"error": f"Invalid parameters JSON: {e}"}, args.format)
            return 2

    defaults: Dict[str, Any] = {
        "sma_short_window": 10,
        "sma_long_window": 30,
        "take_profit_percentage": 0.02,
        "stop_loss_percentage": 0.01,
        "position_size_percentage": 0.1,
        "max_holding_minutes": 60,
        "min_confidence": 0.6,
    }
    params = {**defaults, **params}

    engine = BacktestingEngine(initial_capital=args.initial_capital)
    result = engine.run_backtest(
        strategy_name=args.strategy_name,
        market_data=market_data,
        strategy_params=params,
        execution_mode=args.execution_mode,
    )

    if args.detailed_report:
        simulator = StrategySimulator(args.initial_capital)
        trades, _signals = simulator.simulate_strategy(
            market_data, params, args.execution_mode
        )
        report = ReportGenerator().generate_comprehensive_report(result, trades)
        if args.output_file:
            ReportGenerator().export_to_json(report, args.output_file)
            _print({"saved_to": args.output_file}, args.format)
        else:
            _print(report, args.format)
        return 0

    _print(result.dict(), args.format)
    return 0


def cmd_generate_data(args: argparse.Namespace) -> int:
    data = create_sample_market_data(args.symbol, args.days)
    data.to_csv(args.output_file)
    _print({"message": "Sample data generated", "file": args.output_file}, args.format)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backtesting CLI Tool")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )
    parser.add_argument("--initial-capital", type=float, default=10000)
    sub = parser.add_subparsers(dest="command")

    p_bt = sub.add_parser("backtest", help="Run a backtest")
    p_bt.add_argument("--strategy-name", required=True)
    p_bt.add_argument("--symbol", default="BTCUSDT")
    p_bt.add_argument("--days", type=int, default=30)
    p_bt.add_argument("--data-file")
    p_bt.add_argument("--parameters", help="JSON string of parameters")
    p_bt.add_argument(
        "--execution-mode",
        default="FIRST_SIGNAL",
        choices=["FIRST_SIGNAL", "CONTINUOUS", "ENHANCED"],
    )
    p_bt.add_argument("--detailed-report", action="store_true")
    p_bt.add_argument("--output-file")
    p_bt.set_defaults(func=cmd_backtest)

    p_gen = sub.add_parser("generate-data", help="Generate sample market data CSV")
    p_gen.add_argument("--symbol", default="BTCUSDT")
    p_gen.add_argument("--days", type=int, default=30)
    p_gen.add_argument("--output-file", required=True)
    p_gen.set_defaults(func=cmd_generate_data)

    return parser


def main(argv: List[str] | None = None) -> int:
    # Configure structured logging early
    configure_structlog()
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "version", False):
        print(_get_version())
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
