"""Historical data loader for backtesting engine.

This module provides functionality to load historical market data from various sources
including CSV files, databases, and external APIs for backtesting purposes.
"""

import asyncio
import csv
import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Union, AsyncIterator

import aiofiles
import pandas as pd
from pydantic import BaseModel, Field, validator

from ..models.backtest_result import BacktestResult


class DataSourceConfig(BaseModel):
    """Configuration for data source."""
    source_type: str  # "csv", "database", "api"
    source_path: Optional[str] = None
    connection_string: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    symbols: List[str] = Field(default_factory=list)
    start_date: datetime
    end_date: datetime
    timeframe: str = "1h"  # 1m, 5m, 15m, 1h, 4h, 1d

    @validator('source_type')
    def validate_source_type(cls, v):
        if v not in ["csv", "database", "api"]:
            raise ValueError('source_type must be "csv", "database", or "api"')
        return v

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class HistoricalDataPoint(BaseModel):
    """Single historical market data point."""
    symbol: str
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    quote_volume: Optional[Decimal] = None
    trade_count: Optional[int] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: str
        }

    @validator('open_price', 'high_price', 'low_price', 'close_price')
    def validate_positive_prices(cls, v):
        if v <= 0:
            raise ValueError('All prices must be positive')
        return v

    @validator('volume')
    def validate_volume(cls, v):
        if v < 0:
            raise ValueError('volume must be non-negative')
        return v


class DataLoadResult(BaseModel):
    """Result of data loading operation."""
    total_records: int
    symbols: List[str]
    date_range: Dict[str, datetime]
    timeframe: str
    data_quality_score: float
    missing_periods: List[Dict[str, Union[str, datetime]]]
    load_duration_seconds: float

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HistoricalDataLoader:
    """Loads historical market data for backtesting."""

    def __init__(self, config: DataSourceConfig):
        self.config = config
        self._data_cache: Dict[str, List[HistoricalDataPoint]] = {}

    async def load_data(self) -> DataLoadResult:
        """Load historical data based on configuration.
        
        Returns:
            DataLoadResult with loaded data statistics
        """
        start_time = datetime.utcnow()
        
        if self.config.source_type == "csv":
            data_points = await self._load_from_csv()
        elif self.config.source_type == "database":
            data_points = await self._load_from_database()
        elif self.config.source_type == "api":
            data_points = await self._load_from_api()
        else:
            raise ValueError(f"Unsupported source type: {self.config.source_type}")

        # Cache the loaded data
        self._organize_data_by_symbol(data_points)
        
        # Calculate statistics
        end_time = datetime.utcnow()
        load_duration = (end_time - start_time).total_seconds()
        
        symbols = list(set(point.symbol for point in data_points))
        date_range = self._calculate_date_range(data_points)
        missing_periods = await self._detect_missing_periods(data_points)
        quality_score = self._calculate_data_quality_score(data_points, missing_periods)

        return DataLoadResult(
            total_records=len(data_points),
            symbols=symbols,
            date_range=date_range,
            timeframe=self.config.timeframe,
            data_quality_score=quality_score,
            missing_periods=missing_periods,
            load_duration_seconds=load_duration
        )

    async def get_data_for_symbol(self, symbol: str, 
                                 start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> List[HistoricalDataPoint]:
        """Get historical data for a specific symbol and date range.
        
        Args:
            symbol: Trading symbol
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            
        Returns:
            List of historical data points
        """
        if symbol not in self._data_cache:
            raise ValueError(f"No data available for symbol: {symbol}")

        data = self._data_cache[symbol]
        
        if start_date or end_date:
            filtered_data = []
            for point in data:
                if start_date and point.timestamp < start_date:
                    continue
                if end_date and point.timestamp > end_date:
                    continue
                filtered_data.append(point)
            return filtered_data
            
        return data

    async def get_data_stream(self, symbol: str,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> AsyncIterator[HistoricalDataPoint]:
        """Stream historical data for a symbol.
        
        Args:
            symbol: Trading symbol
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            
        Yields:
            HistoricalDataPoint objects in chronological order
        """
        data = await self.get_data_for_symbol(symbol, start_date, end_date)
        
        # Sort by timestamp to ensure chronological order
        sorted_data = sorted(data, key=lambda x: x.timestamp)
        
        for point in sorted_data:
            yield point
            # Simulate real-time streaming with small delay
            await asyncio.sleep(0.001)

    async def _load_from_csv(self) -> List[HistoricalDataPoint]:
        """Load data from CSV file."""
        if not self.config.source_path:
            raise ValueError("source_path required for CSV data source")

        csv_path = Path(self.config.source_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        data_points = []
        
        async with aiofiles.open(csv_path, mode='r') as file:
            content = await file.read()
            
        # Parse CSV content
        csv_reader = csv.DictReader(content.splitlines())
        
        for row in csv_reader:
            try:
                # Convert timestamp
                timestamp = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                
                # Filter by date range
                if timestamp < self.config.start_date or timestamp > self.config.end_date:
                    continue
                
                # Filter by symbols if specified
                symbol = row['symbol']
                if self.config.symbols and symbol not in self.config.symbols:
                    continue

                data_point = HistoricalDataPoint(
                    symbol=symbol,
                    timestamp=timestamp,
                    open_price=Decimal(row['open_price']),
                    high_price=Decimal(row['high_price']),
                    low_price=Decimal(row['low_price']),
                    close_price=Decimal(row['close_price']),
                    volume=Decimal(row['volume']),
                    quote_volume=Decimal(row.get('quote_volume', '0')),
                    trade_count=int(row.get('trade_count', 0))
                )
                data_points.append(data_point)
                
            except (KeyError, ValueError, TypeError) as e:
                # Skip invalid rows
                continue

        return data_points

    async def _load_from_database(self) -> List[HistoricalDataPoint]:
        """Load data from database."""
        # Placeholder for database implementation
        # In a real implementation, this would connect to PostgreSQL/InfluxDB
        raise NotImplementedError("Database loading not implemented yet")

    async def _load_from_api(self) -> List[HistoricalDataPoint]:
        """Load data from external API."""
        # Placeholder for API implementation
        # In a real implementation, this would fetch from Binance/other exchanges
        raise NotImplementedError("API loading not implemented yet")

    def _organize_data_by_symbol(self, data_points: List[HistoricalDataPoint]) -> None:
        """Organize data points by symbol in cache."""
        self._data_cache.clear()
        
        for point in data_points:
            if point.symbol not in self._data_cache:
                self._data_cache[point.symbol] = []
            self._data_cache[point.symbol].append(point)

    def _calculate_date_range(self, data_points: List[HistoricalDataPoint]) -> Dict[str, datetime]:
        """Calculate the actual date range of loaded data."""
        if not data_points:
            return {"start": self.config.start_date, "end": self.config.end_date}
            
        timestamps = [point.timestamp for point in data_points]
        return {
            "start": min(timestamps),
            "end": max(timestamps)
        }

    async def _detect_missing_periods(self, data_points: List[HistoricalDataPoint]) -> List[Dict[str, Union[str, datetime]]]:
        """Detect missing data periods for each symbol."""
        missing_periods = []
        
        for symbol in set(point.symbol for point in data_points):
            symbol_data = [point for point in data_points if point.symbol == symbol]
            symbol_data.sort(key=lambda x: x.timestamp)
            
            # Calculate expected interval based on timeframe
            if self.config.timeframe == "1m":
                expected_interval = timedelta(minutes=1)
            elif self.config.timeframe == "5m":
                expected_interval = timedelta(minutes=5)
            elif self.config.timeframe == "15m":
                expected_interval = timedelta(minutes=15)
            elif self.config.timeframe == "1h":
                expected_interval = timedelta(hours=1)
            elif self.config.timeframe == "4h":
                expected_interval = timedelta(hours=4)
            elif self.config.timeframe == "1d":
                expected_interval = timedelta(days=1)
            else:
                continue  # Skip unknown timeframes
            
            # Check for gaps
            for i in range(1, len(symbol_data)):
                current_time = symbol_data[i].timestamp
                previous_time = symbol_data[i-1].timestamp
                
                expected_next_time = previous_time + expected_interval
                gap_duration = current_time - expected_next_time
                
                # If gap is larger than expected interval, it's missing data
                if gap_duration > expected_interval:
                    missing_periods.append({
                        "symbol": symbol,
                        "start": expected_next_time,
                        "end": current_time - expected_interval,
                        "duration_hours": gap_duration.total_seconds() / 3600
                    })
        
        return missing_periods

    def _calculate_data_quality_score(self, data_points: List[HistoricalDataPoint], 
                                    missing_periods: List[Dict[str, Union[str, datetime]]]) -> float:
        """Calculate data quality score (0.0 to 1.0)."""
        if not data_points:
            return 0.0
        
        # Calculate total expected data points
        total_duration = self.config.end_date - self.config.start_date
        
        if self.config.timeframe == "1m":
            expected_points = total_duration.total_seconds() / 60
        elif self.config.timeframe == "5m":
            expected_points = total_duration.total_seconds() / 300
        elif self.config.timeframe == "15m":
            expected_points = total_duration.total_seconds() / 900
        elif self.config.timeframe == "1h":
            expected_points = total_duration.total_seconds() / 3600
        elif self.config.timeframe == "4h":
            expected_points = total_duration.total_seconds() / 14400
        elif self.config.timeframe == "1d":
            expected_points = total_duration.days
        else:
            return 1.0  # Can't calculate for unknown timeframes
        
        # Account for multiple symbols
        expected_points *= len(self.config.symbols) if self.config.symbols else 1
        
        # Calculate completeness ratio
        actual_points = len(data_points)
        completeness_ratio = min(actual_points / expected_points, 1.0) if expected_points > 0 else 0.0
        
        # Penalize for data quality issues
        quality_penalty = len(missing_periods) * 0.01  # 1% penalty per missing period
        
        return max(completeness_ratio - quality_penalty, 0.0)

    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols in loaded data."""
        return list(self._data_cache.keys())

    def get_data_statistics(self) -> Dict[str, Union[int, float, str]]:
        """Get statistics about loaded data."""
        total_points = sum(len(data) for data in self._data_cache.values())
        symbols_count = len(self._data_cache)
        
        if total_points == 0:
            return {
                "total_data_points": 0,
                "symbols_count": 0,
                "average_points_per_symbol": 0.0,
                "data_quality": "No data loaded"
            }
        
        avg_points = total_points / symbols_count if symbols_count > 0 else 0
        
        return {
            "total_data_points": total_points,
            "symbols_count": symbols_count,
            "average_points_per_symbol": round(avg_points, 2),
            "timeframe": self.config.timeframe,
            "date_range": f"{self.config.start_date.date()} to {self.config.end_date.date()}"
        }