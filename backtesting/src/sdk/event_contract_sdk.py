"""Event Contract Backtesting SDK.

This module provides a comprehensive SDK for event contract backtesting,
including programmatic interfaces, standardized output formats (JSON/Protobuf),
and integration utilities for external systems.
"""

import asyncio
import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable, AsyncIterator
from dataclasses import dataclass, asdict
from enum import Enum

from pydantic import BaseModel, Field, validator
import structlog

from ..engines.parallel_backtest_engine import (
    ParallelBacktestEngine, PerformanceOptimizationConfig, BacktestTask, BacktestTaskResult
)
from ..loaders.binance_event_data_processor import (
    BinanceEventDataProcessor, DataProcessingConfig, TimeFrame, ProcessedDataPoint
)
from ..simulators.event_contract_simulator import EventContractSimulator, EventContractConfig
from ..strategies.event_contract_strategy import (
    BaseEventContractStrategy, EventContractStrategyConfig, EventContractSignal
)
from ..analyzers.volatility_analyzer import VolatilityAnalyzer, VolatilityAnalyzerConfig
from ..models.backtest_result import BacktestResult


logger = structlog.get_logger(__name__)


class OutputFormat(str, Enum):
    """Supported output formats."""
    JSON = "json"
    PROTOBUF = "protobuf"
    CSV = "csv"
    PARQUET = "parquet"
    EXCEL = "excel"


class BacktestMode(str, Enum):
    """Backtesting execution modes."""
    SINGLE_STRATEGY = "single_strategy"      # Single strategy, single symbol
    MULTI_STRATEGY = "multi_strategy"        # Multiple strategies, single symbol
    MULTI_SYMBOL = "multi_symbol"            # Single strategy, multiple symbols
    PORTFOLIO = "portfolio"                  # Multiple strategies, multiple symbols
    OPTIMIZATION = "optimization"            # Parameter optimization


class SDKConfig(BaseModel):
    """SDK configuration."""
    
    # Output configuration
    default_output_format: OutputFormat = OutputFormat.JSON
    output_directory: Path = Field(default=Path("output"))
    include_metadata: bool = True
    compress_output: bool = False
    
    # Performance configuration
    performance_config: PerformanceOptimizationConfig = Field(
        default_factory=PerformanceOptimizationConfig
    )
    
    # Data processing configuration
    data_config: DataProcessingConfig = Field(
        default_factory=DataProcessingConfig
    )
    
    # Logging configuration
    enable_detailed_logging: bool = True
    log_level: str = "INFO"
    log_to_file: bool = True
    
    # Integration settings
    enable_webhooks: bool = False
    webhook_urls: List[str] = Field(default_factory=list)
    
    @validator('output_directory')
    def create_output_directory(cls, v):
        v.mkdir(parents=True, exist_ok=True)
        return v


@dataclass
class BacktestRequest:
    """Backtesting request specification."""
    
    # Basic parameters
    symbols: List[str]
    timeframes: List[TimeFrame]
    start_date: datetime
    end_date: datetime
    
    # Strategy configuration
    strategy_configs: List[EventContractStrategyConfig]
    
    # Execution parameters
    mode: BacktestMode = BacktestMode.SINGLE_STRATEGY
    initial_capital: Decimal = Decimal('10000.0')
    
    # Output configuration
    output_format: OutputFormat = OutputFormat.JSON
    output_filename: Optional[str] = None
    
    # Advanced options
    enable_optimization: bool = False
    optimization_parameters: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbols': self.symbols,
            'timeframes': [tf.value for tf in self.timeframes],
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'strategy_configs': [config.dict() for config in self.strategy_configs],
            'mode': self.mode.value,
            'initial_capital': str(self.initial_capital),
            'output_format': self.output_format.value,
            'output_filename': self.output_filename,
            'enable_optimization': self.enable_optimization,
            'optimization_parameters': self.optimization_parameters or {}
        }


@dataclass
class BacktestResponse:
    """Backtesting response with results and metadata."""
    
    # Request information
    request_id: str
    request: BacktestRequest
    
    # Execution metadata
    execution_start_time: datetime
    execution_end_time: datetime
    execution_duration_seconds: float
    
    # Results
    results: List[BacktestResult]
    task_results: List[BacktestTaskResult]
    
    # Performance statistics
    performance_stats: Dict[str, Any]
    
    # Status information
    success: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'request_id': self.request_id,
            'request': self.request.to_dict(),
            'execution_metadata': {
                'start_time': self.execution_start_time.isoformat(),
                'end_time': self.execution_end_time.isoformat(),
                'duration_seconds': self.execution_duration_seconds
            },
            'results': [result.dict() for result in self.results],
            'task_results': [task_result.to_dict() for task_result in self.task_results],
            'performance_stats': self.performance_stats,
            'status': {
                'success': self.success,
                'error_message': self.error_message,
                'warnings': self.warnings or []
            }
        }


class EventContractBacktestSDK:
    """Comprehensive SDK for event contract backtesting."""
    
    def __init__(self, config: SDKConfig):
        """Initialize the SDK.
        
        Args:
            config: SDK configuration
        """
        self.config = config
        
        # Initialize core components
        self.backtest_engine = ParallelBacktestEngine(config.performance_config)
        self.data_processor = BinanceEventDataProcessor(config.data_config, None)
        
        # Request tracking
        self._active_requests: Dict[str, BacktestRequest] = {}
        self._request_counter = 0
        
        logger.info(
            "EventContractBacktestSDK initialized",
            output_format=config.default_output_format.value,
            output_directory=str(config.output_directory)
        )
    
    async def run_backtest(self, request: BacktestRequest) -> BacktestResponse:
        """Run a comprehensive backtesting session.
        
        Args:
            request: Backtesting request specification
            
        Returns:
            BacktestResponse with results and metadata
        """
        # Generate request ID
        self._request_counter += 1
        request_id = f"backtest_{self._request_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        execution_start = datetime.now()
        
        logger.info(
            "Starting backtesting session",
            request_id=request_id,
            mode=request.mode.value,
            symbols=len(request.symbols),
            strategies=len(request.strategy_configs)
        )
        
        try:
            # Store active request
            self._active_requests[request_id] = request
            
            # Execute based on mode
            if request.mode == BacktestMode.SINGLE_STRATEGY:
                results, task_results = await self._run_single_strategy_backtest(request)
            elif request.mode == BacktestMode.MULTI_STRATEGY:
                results, task_results = await self._run_multi_strategy_backtest(request)
            elif request.mode == BacktestMode.MULTI_SYMBOL:
                results, task_results = await self._run_multi_symbol_backtest(request)
            elif request.mode == BacktestMode.PORTFOLIO:
                results, task_results = await self._run_portfolio_backtest(request)
            elif request.mode == BacktestMode.OPTIMIZATION:
                results, task_results = await self._run_optimization_backtest(request)
            else:
                raise ValueError(f"Unsupported backtest mode: {request.mode}")
            
            execution_end = datetime.now()
            execution_duration = (execution_end - execution_start).total_seconds()
            
            # Get performance statistics
            performance_stats = self.backtest_engine.get_performance_stats()
            
            # Create response
            response = BacktestResponse(
                request_id=request_id,
                request=request,
                execution_start_time=execution_start,
                execution_end_time=execution_end,
                execution_duration_seconds=execution_duration,
                results=results,
                task_results=task_results,
                performance_stats=performance_stats,
                success=True
            )
            
            # Save results
            await self._save_results(response)
            
            # Send webhooks if enabled
            if self.config.enable_webhooks:
                await self._send_webhooks(response)
            
            logger.info(
                "Backtesting session completed",
                request_id=request_id,
                duration_seconds=execution_duration,
                total_results=len(results)
            )
            
            return response
            
        except Exception as e:
            execution_end = datetime.now()
            execution_duration = (execution_end - execution_start).total_seconds()
            
            logger.error(
                "Backtesting session failed",
                request_id=request_id,
                error=str(e),
                duration_seconds=execution_duration
            )
            
            # Create error response
            response = BacktestResponse(
                request_id=request_id,
                request=request,
                execution_start_time=execution_start,
                execution_end_time=execution_end,
                execution_duration_seconds=execution_duration,
                results=[],
                task_results=[],
                performance_stats={},
                success=False,
                error_message=str(e)
            )
            
            return response
            
        finally:
            # Clean up
            if request_id in self._active_requests:
                del self._active_requests[request_id]
    
    async def _run_single_strategy_backtest(self, request: BacktestRequest) -> Tuple[List[BacktestResult], List[BacktestTaskResult]]:
        """Run single strategy backtesting."""
        if len(request.strategy_configs) != 1:
            raise ValueError("Single strategy mode requires exactly one strategy configuration")
        
        strategy_config = request.strategy_configs[0]
        tasks = []
        
        # Create tasks for each symbol and timeframe combination
        for symbol in request.symbols:
            for timeframe in request.timeframes:
                # Load data for this combination
                data_points = await self._load_data_for_task(
                    symbol, timeframe, request.start_date, request.end_date
                )
                
                if data_points:
                    task = BacktestTask(
                        task_id=f"{symbol}_{timeframe.value}_{strategy_config.name}",
                        symbol=symbol,
                        timeframe=timeframe,
                        start_date=request.start_date,
                        end_date=request.end_date,
                        strategy_config=strategy_config,
                        data_points=data_points
                    )
                    tasks.append(task)
        
        # Execute tasks
        task_results = await self.backtest_engine.run_parallel_backtest(tasks)
        
        # Extract successful results
        results = []
        for task_result in task_results:
            if task_result.success and task_result.result:
                results.append(task_result.result)
        
        return results, task_results
    
    async def _run_multi_strategy_backtest(self, request: BacktestRequest) -> Tuple[List[BacktestResult], List[BacktestTaskResult]]:
        """Run multi-strategy backtesting."""
        if len(request.symbols) != 1:
            raise ValueError("Multi-strategy mode requires exactly one symbol")
        
        symbol = request.symbols[0]
        tasks = []
        
        # Create tasks for each strategy and timeframe combination
        for strategy_config in request.strategy_configs:
            for timeframe in request.timeframes:
                # Load data for this combination
                data_points = await self._load_data_for_task(
                    symbol, timeframe, request.start_date, request.end_date
                )
                
                if data_points:
                    task = BacktestTask(
                        task_id=f"{symbol}_{timeframe.value}_{strategy_config.name}",
                        symbol=symbol,
                        timeframe=timeframe,
                        start_date=request.start_date,
                        end_date=request.end_date,
                        strategy_config=strategy_config,
                        data_points=data_points
                    )
                    tasks.append(task)
        
        # Execute tasks
        task_results = await self.backtest_engine.run_parallel_backtest(tasks)
        
        # Extract successful results
        results = []
        for task_result in task_results:
            if task_result.success and task_result.result:
                results.append(task_result.result)
        
        return results, task_results
    
    async def _run_multi_symbol_backtest(self, request: BacktestRequest) -> Tuple[List[BacktestResult], List[BacktestTaskResult]]:
        """Run multi-symbol backtesting."""
        if len(request.strategy_configs) != 1:
            raise ValueError("Multi-symbol mode requires exactly one strategy configuration")
        
        strategy_config = request.strategy_configs[0]
        tasks = []
        
        # Create tasks for each symbol and timeframe combination
        for symbol in request.symbols:
            for timeframe in request.timeframes:
                # Load data for this combination
                data_points = await self._load_data_for_task(
                    symbol, timeframe, request.start_date, request.end_date
                )
                
                if data_points:
                    task = BacktestTask(
                        task_id=f"{symbol}_{timeframe.value}_{strategy_config.name}",
                        symbol=symbol,
                        timeframe=timeframe,
                        start_date=request.start_date,
                        end_date=request.end_date,
                        strategy_config=strategy_config,
                        data_points=data_points
                    )
                    tasks.append(task)
        
        # Execute tasks
        task_results = await self.backtest_engine.run_parallel_backtest(tasks)
        
        # Extract successful results
        results = []
        for task_result in task_results:
            if task_result.success and task_result.result:
                results.append(task_result.result)
        
        return results, task_results
    
    async def _run_portfolio_backtest(self, request: BacktestRequest) -> Tuple[List[BacktestResult], List[BacktestTaskResult]]:
        """Run portfolio backtesting (multiple strategies, multiple symbols)."""
        tasks = []
        
        # Create tasks for all combinations
        for symbol in request.symbols:
            for strategy_config in request.strategy_configs:
                for timeframe in request.timeframes:
                    # Load data for this combination
                    data_points = await self._load_data_for_task(
                        symbol, timeframe, request.start_date, request.end_date
                    )
                    
                    if data_points:
                        task = BacktestTask(
                            task_id=f"{symbol}_{timeframe.value}_{strategy_config.name}",
                            symbol=symbol,
                            timeframe=timeframe,
                            start_date=request.start_date,
                            end_date=request.end_date,
                            strategy_config=strategy_config,
                            data_points=data_points
                        )
                        tasks.append(task)
        
        # Execute tasks
        task_results = await self.backtest_engine.run_parallel_backtest(tasks)
        
        # Extract successful results
        results = []
        for task_result in task_results:
            if task_result.success and task_result.result:
                results.append(task_result.result)
        
        return results, task_results
    
    async def _run_optimization_backtest(self, request: BacktestRequest) -> Tuple[List[BacktestResult], List[BacktestTaskResult]]:
        """Run parameter optimization backtesting."""
        if not request.enable_optimization or not request.optimization_parameters:
            raise ValueError("Optimization mode requires optimization parameters")
        
        # Generate parameter combinations
        param_combinations = self._generate_parameter_combinations(request.optimization_parameters)
        
        tasks = []
        
        # Create tasks for each parameter combination
        for i, params in enumerate(param_combinations):
            for symbol in request.symbols:
                for timeframe in request.timeframes:
                    # Create modified strategy config with optimization parameters
                    strategy_config = request.strategy_configs[0].copy(deep=True)
                    strategy_config.custom_parameters.update(params)
                    strategy_config.name = f"{strategy_config.name}_opt_{i}"
                    
                    # Load data for this combination
                    data_points = await self._load_data_for_task(
                        symbol, timeframe, request.start_date, request.end_date
                    )
                    
                    if data_points:
                        task = BacktestTask(
                            task_id=f"{symbol}_{timeframe.value}_{strategy_config.name}",
                            symbol=symbol,
                            timeframe=timeframe,
                            start_date=request.start_date,
                            end_date=request.end_date,
                            strategy_config=strategy_config,
                            data_points=data_points
                        )
                        tasks.append(task)
        
        # Execute tasks
        task_results = await self.backtest_engine.run_parallel_backtest(tasks)
        
        # Extract successful results
        results = []
        for task_result in task_results:
            if task_result.success and task_result.result:
                results.append(task_result.result)
        
        return results, task_results
    
    def _generate_parameter_combinations(self, optimization_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate all parameter combinations for optimization."""
        import itertools
        
        param_names = list(optimization_params.keys())
        param_values = [optimization_params[name] for name in param_names]
        
        combinations = []
        for combination in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combination))
            combinations.append(param_dict)
        
        return combinations
    
    async def _load_data_for_task(self, symbol: str, timeframe: TimeFrame,
                                 start_date: datetime, end_date: datetime) -> List[ProcessedDataPoint]:
        """Load and process data for a specific task."""
        try:
            data_points = await self.data_processor.process_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            return data_points
        except Exception as e:
            logger.error(
                "Failed to load data for task",
                symbol=symbol,
                timeframe=timeframe.value,
                error=str(e)
            )
            return []
    
    async def _save_results(self, response: BacktestResponse) -> None:
        """Save backtesting results to file."""
        try:
            # Determine output filename
            if response.request.output_filename:
                filename = response.request.output_filename
            else:
                timestamp = response.execution_start_time.strftime('%Y%m%d_%H%M%S')
                filename = f"backtest_results_{response.request_id}_{timestamp}"
            
            # Save based on output format
            output_format = response.request.output_format
            
            if output_format == OutputFormat.JSON:
                await self._save_json_results(response, filename)
            elif output_format == OutputFormat.CSV:
                await self._save_csv_results(response, filename)
            elif output_format == OutputFormat.PARQUET:
                await self._save_parquet_results(response, filename)
            elif output_format == OutputFormat.EXCEL:
                await self._save_excel_results(response, filename)
            # Note: Protobuf support would be added here
            
        except Exception as e:
            logger.error(
                "Failed to save results",
                request_id=response.request_id,
                error=str(e)
            )
    
    async def _save_json_results(self, response: BacktestResponse, filename: str) -> None:
        """Save results in JSON format."""
        output_file = self.config.output_directory / f"{filename}.json"
        
        with open(output_file, 'w') as f:
            json.dump(response.to_dict(), f, indent=2, default=str)
        
        logger.info("Results saved to JSON", file=str(output_file))
    
    async def _save_csv_results(self, response: BacktestResponse, filename: str) -> None:
        """Save results in CSV format."""
        import pandas as pd
        
        # Convert results to DataFrame
        results_data = []
        for result in response.results:
            result_dict = result.dict()
            result_dict['request_id'] = response.request_id
            results_data.append(result_dict)
        
        if results_data:
            df = pd.DataFrame(results_data)
            output_file = self.config.output_directory / f"{filename}.csv"
            df.to_csv(output_file, index=False)
            
            logger.info("Results saved to CSV", file=str(output_file))
    
    async def _save_parquet_results(self, response: BacktestResponse, filename: str) -> None:
        """Save results in Parquet format."""
        import pandas as pd
        
        # Convert results to DataFrame
        results_data = []
        for result in response.results:
            result_dict = result.dict()
            result_dict['request_id'] = response.request_id
            results_data.append(result_dict)
        
        if results_data:
            df = pd.DataFrame(results_data)
            output_file = self.config.output_directory / f"{filename}.parquet"
            df.to_parquet(output_file, index=False)
            
            logger.info("Results saved to Parquet", file=str(output_file))
    
    async def _save_excel_results(self, response: BacktestResponse, filename: str) -> None:
        """Save results in Excel format."""
        import pandas as pd
        
        output_file = self.config.output_directory / f"{filename}.xlsx"
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Results sheet
            results_data = []
            for result in response.results:
                result_dict = result.dict()
                result_dict['request_id'] = response.request_id
                results_data.append(result_dict)
            
            if results_data:
                results_df = pd.DataFrame(results_data)
                results_df.to_excel(writer, sheet_name='Results', index=False)
            
            # Task results sheet
            task_data = [task_result.to_dict() for task_result in response.task_results]
            if task_data:
                task_df = pd.DataFrame(task_data)
                task_df.to_excel(writer, sheet_name='Task_Results', index=False)
            
            # Performance stats sheet
            perf_data = [{'metric': k, 'value': v} for k, v in response.performance_stats.items()]
            if perf_data:
                perf_df = pd.DataFrame(perf_data)
                perf_df.to_excel(writer, sheet_name='Performance', index=False)
        
        logger.info("Results saved to Excel", file=str(output_file))
    
    async def _send_webhooks(self, response: BacktestResponse) -> None:
        """Send webhook notifications."""
        if not self.config.webhook_urls:
            return
        
        import aiohttp
        
        webhook_data = {
            'request_id': response.request_id,
            'success': response.success,
            'execution_duration': response.execution_duration_seconds,
            'total_results': len(response.results),
            'timestamp': response.execution_end_time.isoformat()
        }
        
        async with aiohttp.ClientSession() as session:
            for webhook_url in self.config.webhook_urls:
                try:
                    async with session.post(webhook_url, json=webhook_data) as resp:
                        if resp.status == 200:
                            logger.info("Webhook sent successfully", url=webhook_url)
                        else:
                            logger.warning(
                                "Webhook failed",
                                url=webhook_url,
                                status=resp.status
                            )
                except Exception as e:
                    logger.error(
                        "Webhook error",
                        url=webhook_url,
                        error=str(e)
                    )
    
    def get_active_requests(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active requests."""
        return {
            request_id: request.to_dict()
            for request_id, request in self._active_requests.items()
        }
    
    def get_sdk_status(self) -> Dict[str, Any]:
        """Get SDK status and statistics."""
        return {
            'active_requests': len(self._active_requests),
            'total_requests_processed': self._request_counter,
            'engine_stats': self.backtest_engine.get_performance_stats(),
            'data_processor_stats': self.data_processor.get_cache_statistics(),
            'config': {
                'output_format': self.config.default_output_format.value,
                'output_directory': str(self.config.output_directory),
                'performance_mode': self.config.performance_config.processing_mode.value
            }
        }
    
    async def clear_caches(self) -> Dict[str, Any]:
        """Clear all caches and return statistics."""
        # Get stats before clearing
        engine_stats = self.backtest_engine.get_performance_stats()
        data_stats = self.data_processor.get_cache_statistics()
        
        # Clear caches
        self.backtest_engine.clear_caches()
        await self.data_processor.clear_cache()
        
        return {
            'engine_cache_cleared': True,
            'data_cache_cleared': True,
            'previous_engine_stats': engine_stats,
            'previous_data_stats': data_stats
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of all components."""
        health_status = {
            'sdk': 'healthy',
            'backtest_engine': 'healthy',
            'data_processor': 'healthy',
            'output_directory': 'healthy',
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Check output directory
            if not self.config.output_directory.exists():
                health_status['output_directory'] = 'error: directory not found'
            elif not self.config.output_directory.is_dir():
                health_status['output_directory'] = 'error: not a directory'
            
            # Check engine status
            engine_stats = self.backtest_engine.get_performance_stats()
            if not engine_stats:
                health_status['backtest_engine'] = 'warning: no statistics available'
            
            # Check data processor
            data_stats = self.data_processor.get_cache_statistics()
            if not data_stats.get('caching_enabled', False):
                health_status['data_processor'] = 'warning: caching disabled'
            
        except Exception as e:
            health_status['sdk'] = f'error: {str(e)}'
        
        return health_status