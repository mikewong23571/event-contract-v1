#!/usr/bin/env python3
"""Event Contract Backtesting CLI

Enhanced CLI for event contract backtesting with support for parallel processing,
multiple output formats, and advanced strategy configuration.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from pydantic import ValidationError

from ..sdk.event_contract_sdk import (
    EventContractBacktestSDK, SDKConfig, BacktestRequest, BacktestMode, OutputFormat
)
from ..loaders.binance_event_data_processor import TimeFrame
from ..strategies.event_contract_strategy import EventContractStrategyConfig
from ..engines.parallel_backtest_engine import PerformanceOptimizationConfig, ProcessingMode
from ..config.logging import configure_structlog
from ._utils import get_version, print_output


PACKAGE_NAME = "event-contract-backtesting"
DEFAULT_VERSION = "0.1.0"


async def cmd_backtest(args: argparse.Namespace) -> int:
    """Run event contract backtesting."""
    try:
        # Parse symbols
        symbols = [s.strip() for s in args.symbols.split(',')]
        
        # Parse timeframes
        timeframes = []
        for tf_str in args.timeframes.split(','):
            try:
                timeframes.append(TimeFrame(tf_str.strip()))
            except ValueError:
                print_output({"error": f"Invalid timeframe: {tf_str}"}, args.format)
                return 2
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(args.start_date)
            end_date = datetime.fromisoformat(args.end_date)
        except ValueError as e:
            print_output({"error": f"Invalid date format: {e}"}, args.format)
            return 2
        
        # Parse strategy configuration
        strategy_config = EventContractStrategyConfig(
            name=args.strategy_name,
            description=args.strategy_description or f"CLI strategy: {args.strategy_name}"
        )
        
        # Parse custom parameters
        if args.parameters:
            try:
                custom_params = json.loads(args.parameters)
                strategy_config.custom_parameters.update(custom_params)
            except json.JSONDecodeError as e:
                print_output({"error": f"Invalid parameters JSON: {e}"}, args.format)
                return 2
        
        # Parse output format
        try:
            output_format = OutputFormat(args.output_format)
        except ValueError:
            print_output({"error": f"Invalid output format: {args.output_format}"}, args.format)
            return 2
        
        # Parse backtest mode
        try:
            mode = BacktestMode(args.mode)
        except ValueError:
            print_output({"error": f"Invalid backtest mode: {args.mode}"}, args.format)
            return 2
        
        # Create SDK configuration
        perf_config = PerformanceOptimizationConfig(
            processing_mode=ProcessingMode(args.processing_mode),
            max_workers=args.max_workers
        )
        
        sdk_config = SDKConfig(
            default_output_format=output_format,
            output_directory=Path(args.output_dir),
            performance_config=perf_config
        )
        
        # Create backtesting request
        request = BacktestRequest(
            symbols=symbols,
            timeframes=timeframes,
            start_date=start_date,
            end_date=end_date,
            strategy_configs=[strategy_config],
            mode=mode,
            initial_capital=Decimal(str(args.initial_capital)),
            output_format=output_format,
            output_filename=args.output_file
        )
        
        # Initialize SDK and run backtest
        sdk = EventContractBacktestSDK(sdk_config)
        response = await sdk.run_backtest(request)
        
        # Output results
        if args.format == "json":
            print_output(response.to_dict(), args.format)
        else:
            # Human-readable summary
            summary = {
                "request_id": response.request_id,
                "success": response.success,
                "execution_time": f"{response.execution_duration_seconds:.2f}s",
                "total_results": len(response.results),
                "successful_tasks": len([r for r in response.task_results if r.success]),
                "failed_tasks": len([r for r in response.task_results if not r.success])
            }
            
            if response.results:
                # Add performance summary
                total_pnl = sum(float(r.total_profit_loss) for r in response.results)
                avg_win_rate = sum(float(r.win_rate) for r in response.results) / len(response.results)
                
                summary.update({
                    "total_pnl": f"{total_pnl:.2f}",
                    "average_win_rate": f"{avg_win_rate:.2%}",
                    "best_strategy": max(response.results, key=lambda r: r.total_profit_loss).strategy_name
                })
            
            if response.error_message:
                summary["error"] = response.error_message
            
            print_output(summary, args.format)
        
        return 0 if response.success else 1
        
    except Exception as e:
        print_output({"error": f"Backtesting failed: {str(e)}"}, args.format)
        return 2


async def cmd_health_check(args: argparse.Namespace) -> int:
    """Perform health check of the backtesting system."""
    try:
        sdk_config = SDKConfig()
        sdk = EventContractBacktestSDK(sdk_config)
        
        health_status = await sdk.health_check()
        print_output(health_status, args.format)
        
        # Return error code if any component is unhealthy
        for component, status in health_status.items():
            if isinstance(status, str) and ('error' in status or 'warning' in status):
                return 1
        
        return 0
        
    except Exception as e:
        print_output({"error": f"Health check failed: {str(e)}"}, args.format)
        return 2


async def cmd_clear_cache(args: argparse.Namespace) -> int:
    """Clear all caches."""
    try:
        sdk_config = SDKConfig()
        sdk = EventContractBacktestSDK(sdk_config)
        
        cache_stats = await sdk.clear_caches()
        print_output(cache_stats, args.format)
        
        return 0
        
    except Exception as e:
        print_output({"error": f"Cache clearing failed: {str(e)}"}, args.format)
        return 2


async def cmd_status(args: argparse.Namespace) -> int:
    """Get SDK status and statistics."""
    try:
        sdk_config = SDKConfig()
        sdk = EventContractBacktestSDK(sdk_config)
        
        status = sdk.get_sdk_status()
        print_output(status, args.format)
        
        return 0
        
    except Exception as e:
        print_output({"error": f"Status check failed: {str(e)}"}, args.format)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Event Contract Backtesting CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic single strategy backtest
  backtest --strategy-name "volatility_strategy" --symbols "BTCUSDT" --timeframes "15m" \
           --start-date "2024-01-01" --end-date "2024-01-31"
  
  # Multi-symbol portfolio backtest
  backtest --strategy-name "portfolio_strategy" --symbols "BTCUSDT,ETHUSDT,ADAUSDT" \
           --timeframes "15m,1h" --mode "multi_symbol" --processing-mode "PARALLEL_THREAD"
  
  # Parameter optimization
  backtest --strategy-name "optimized_strategy" --symbols "BTCUSDT" --timeframes "15m" \
           --mode "optimization" --parameters '{"param1": [1, 2, 3], "param2": [0.1, 0.2]}'
"""
    )
    
    # Global arguments
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument(
        "--format", choices=["json", "text"], default="text", help="Output format"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    # Subcommands
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # Backtest command
    p_bt = sub.add_parser("backtest", help="Run event contract backtesting")
    
    # Required arguments
    p_bt.add_argument("--strategy-name", required=True, help="Strategy name")
    p_bt.add_argument("--symbols", required=True, help="Comma-separated list of symbols (e.g., BTCUSDT,ETHUSDT)")
    p_bt.add_argument("--timeframes", required=True, help="Comma-separated list of timeframes (e.g., 15m,1h)")
    p_bt.add_argument("--start-date", required=True, help="Start date (ISO format: 2024-01-01)")
    p_bt.add_argument("--end-date", required=True, help="End date (ISO format: 2024-01-31)")
    
    # Optional arguments
    p_bt.add_argument("--strategy-description", help="Strategy description")
    p_bt.add_argument("--initial-capital", type=float, default=10000.0, help="Initial capital (default: 10000)")
    p_bt.add_argument("--parameters", help="JSON string of strategy parameters")
    
    # Execution mode
    p_bt.add_argument(
        "--mode",
        choices=["single_strategy", "multi_strategy", "multi_symbol", "portfolio", "optimization"],
        default="single_strategy",
        help="Backtesting mode (default: single_strategy)"
    )
    
    # Processing configuration
    p_bt.add_argument(
        "--processing-mode",
        choices=["SEQUENTIAL", "PARALLEL_THREAD", "PARALLEL_PROCESS", "HYBRID"],
        default="PARALLEL_THREAD",
        help="Processing mode (default: PARALLEL_THREAD)"
    )
    p_bt.add_argument("--max-workers", type=int, default=4, help="Maximum worker threads/processes")
    
    # Output configuration
    p_bt.add_argument(
        "--output-format",
        choices=["json", "csv", "parquet", "excel"],
        default="json",
        help="Output file format (default: json)"
    )
    p_bt.add_argument("--output-file", help="Output filename (without extension)")
    p_bt.add_argument("--output-dir", default="output", help="Output directory (default: output)")
    
    p_bt.set_defaults(func=cmd_backtest)

    # Health check command
    p_health = sub.add_parser("health", help="Perform system health check")
    p_health.set_defaults(func=cmd_health_check)

    # Clear cache command
    p_cache = sub.add_parser("clear-cache", help="Clear all caches")
    p_cache.set_defaults(func=cmd_clear_cache)

    # Status command
    p_status = sub.add_parser("status", help="Get system status and statistics")
    p_status.set_defaults(func=cmd_status)

    return parser


def main(argv: List[str] | None = None) -> int:
    # Configure structured logging early
    configure_structlog()
    parser = build_parser()
    args = parser.parse_args(argv)

    if getattr(args, "version", False):
        print(get_version(PACKAGE_NAME, DEFAULT_VERSION))
        return 0

    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    try:
        # Run async commands
        if asyncio.iscoroutinefunction(args.func):
            return asyncio.run(args.func(args))
        else:
            return int(args.func(args))  # type: ignore[attr-defined]
    except KeyboardInterrupt:  # pragma: no cover
        print_output({"message": "Operation cancelled by user"}, getattr(args, 'format', 'text'))
        return 130
    except Exception as e:
        print_output({"error": f"Unexpected error: {str(e)}"}, getattr(args, 'format', 'text'))
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
