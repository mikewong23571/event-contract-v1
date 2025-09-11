#!/usr/bin/env python3
"""Market Data CLI

Provides a lightweight CLI wrapper around data ingestion/transformation
capabilities with constitutional flags and JSON/text output.

Commands intentionally scoped to core use cases:
- ingest: fetch a small batch for symbols
- historical: ingest historical range and optionally write to file
- validate: quality checks for a batch

Additional functions exist in the library (`backend/src/lib/data_ingestion/`),
but are not duplicated here to avoid scope creep.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from typing import Any, Dict, List

from ..lib.data_ingestion.data_ingester import DataIngester
from ..lib.data_ingestion.data_validator import DataValidator
from ..lib.data_ingestion.market_data_fetcher import MarketDataFetcher
from ._utils import get_version, print_output


PACKAGE_NAME = "event-contract-backend"
DEFAULT_VERSION = "0.1.0"


def cmd_ingest(args: argparse.Namespace) -> int:
    ingester = DataIngester(max_workers=args.workers)
    symbols: List[str] = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    data = ingester.ingest_market_data(symbols=symbols, timeframe=args.timeframe, limit=args.limit)
    stats = ingester.get_ingestion_statistics(
        {sym: [md for md in data if md.symbol == sym] for sym in symbols}
    )
    payload = {
        "symbols": symbols,
        "records": len(data),
        "statistics": stats,
    }
    print_output(payload, args.format)
    return 0


def cmd_historical(args: argparse.Namespace) -> int:
    ingester = DataIngester()
    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    end = datetime.strptime(args.end_date, "%Y-%m-%d")
    data = ingester.ingest_historical_data(
        symbol=args.symbol.upper(), start_date=start, end_date=end, timeframe=args.timeframe
    )

    payload: Dict[str, Any] = {
        "symbol": args.symbol.upper(),
        "records": len(data),
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "sample": [md.dict() for md in data[: min(3, len(data))]],
    }

    if args.output_file:
        with open(args.output_file, "w") as f:
            json.dump([md.dict() for md in data], f, indent=2, default=str)
        payload["saved_to"] = args.output_file
    print_output(payload, args.format)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    validator = DataValidator()
    if args.input_file:
        with open(args.input_file, "r") as f:
            raw = json.load(f)
    else:
        raw = MarketDataFetcher().fetch_ohlcv_data(args.symbol.upper(), args.timeframe, args.limit)

    result = validator.validate_market_data_batch(
        batch=raw, symbol=args.symbol.upper(), timeframe=args.timeframe
    )
    score = validator.get_data_quality_score(result)
    fixes = validator.suggest_data_fixes(result)
    print_output({"validation_result": result, "quality_score": score, "suggestions": fixes}, args.format)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Market Data CLI Tool")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument(
        "--format", choices=["json", "text"], default="json", help="Output format"
    )
    sub = parser.add_subparsers(dest="command")

    p_ing = sub.add_parser("ingest", help="Ingest market data for symbols")
    p_ing.add_argument("--symbols", required=True, help="Comma-separated symbols")
    p_ing.add_argument("--timeframe", default="1m")
    p_ing.add_argument("--limit", type=int, default=100)
    p_ing.add_argument("--workers", type=int, default=4)
    p_ing.set_defaults(func=cmd_ingest)

    p_hist = sub.add_parser("historical", help="Ingest historical data for a symbol")
    p_hist.add_argument("--symbol", required=True)
    p_hist.add_argument("--start-date", required=True, help="YYYY-MM-DD")
    p_hist.add_argument("--end-date", required=True, help="YYYY-MM-DD")
    p_hist.add_argument("--timeframe", default="1m")
    p_hist.add_argument("--output-file")
    p_hist.set_defaults(func=cmd_historical)

    p_val = sub.add_parser("validate", help="Validate data quality for a batch")
    p_val.add_argument("--symbol", required=True)
    p_val.add_argument("--timeframe", default="1m")
    p_val.add_argument("--limit", type=int, default=100)
    p_val.add_argument("--input-file", help="Optional input JSON file")
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
