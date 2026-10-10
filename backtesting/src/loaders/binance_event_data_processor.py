"""Binance Event Contract Data Processor.

This module provides standardized processing for Binance event contract historical data,
with support for multi-timeframe caching and data normalization optimized for
event contract backtesting requirements.
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, AsyncIterator
from dataclasses import dataclass
from enum import Enum

import aiofiles
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, validator
import structlog

from .data_loader import HistoricalDataPoint
from .binance_client import BinanceDataClient


logger = structlog.get_logger(__name__)


class TimeFrame(str, Enum):
    """Supported timeframes for event contract analysis."""
    M1 = "1m"    # 1 minute - for high-frequency analysis
    M5 = "5m"    # 5 minutes - for short-term patterns
    M15 = "15m"  # 15 minutes - for medium-term trends
    M30 = "30m"  # 30 minutes - for trend confirmation
    H1 = "1h"    # 1 hour - for longer-term context
    H4 = "4h"    # 4 hours - for daily pattern analysis
    D1 = "1d"    # 1 day - for weekly pattern analysis


class DataQuality(str, Enum):
    """Data quality levels."""
    EXCELLENT = "EXCELLENT"  # >99% completeness, no gaps
    GOOD = "GOOD"           # >95% completeness, minor gaps
    FAIR = "FAIR"           # >90% completeness, some gaps
    POOR = "POOR"           # <90% completeness, significant gaps


@dataclass
class CacheMetadata:
    """Metadata for cached data."""
    symbol: str
    timeframe: TimeFrame
    start_date: datetime
    end_date: datetime
    total_records: int
    cache_created: datetime
    data_quality: DataQuality
    checksum: str
    file_size_bytes: int


class DataProcessingConfig(BaseModel):
    """Configuration for data processing."""
    
    # Cache settings
    cache_directory: Path = Field(default=Path("data/cache"))
    enable_caching: bool = True
    cache_compression: bool = True
    max_cache_age_hours: int = 24
    
    # Data quality settings
    min_data_quality: DataQuality = DataQuality.FAIR
    max_gap_minutes: int = 60  # Maximum acceptable gap in minutes
    outlier_detection: bool = True
    outlier_threshold_std: float = 4.0  # Standard deviations for outlier detection
    
    # Processing settings
    batch_size: int = 10000  # Records per batch for processing
    parallel_processing: bool = True
    max_workers: int = 4
    
    # Validation settings
    validate_price_consistency: bool = True
    validate_volume_consistency: bool = True
    min_volume_threshold: Decimal = Decimal('0.01')
    
    @validator('cache_directory')
    def validate_cache_directory(cls, v):
        v.mkdir(parents=True, exist_ok=True)
        return v


class ProcessedDataPoint(BaseModel):
    """Enhanced data point with additional processing metadata."""
    
    # Base data
    symbol: str
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    
    # Enhanced fields for event contract analysis
    price_change: Decimal  # Absolute price change from previous period
    price_change_pct: Decimal  # Percentage price change
    volatility: Decimal  # Period volatility (high-low)/close
    volume_ratio: Decimal  # Volume vs average volume
    
    # Technical indicators (basic)
    sma_5: Optional[Decimal] = None
    sma_20: Optional[Decimal] = None
    rsi_14: Optional[Decimal] = None
    
    # Data quality flags
    is_outlier: bool = False
    has_gaps_before: bool = False
    interpolated: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: str
        }


class BinanceEventDataProcessor:
    """Processes Binance data for event contract backtesting."""
    
    def __init__(self, config: DataProcessingConfig, binance_client: Optional[BinanceDataClient] = None):
        self.config = config
        self.binance_client = binance_client
        self._cache_metadata: Dict[str, CacheMetadata] = {}
        self._processed_data_cache: Dict[str, List[ProcessedDataPoint]] = {}
        
        # Initialize cache directory
        self.config.cache_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "BinanceEventDataProcessor initialized",
            cache_directory=str(self.config.cache_directory),
            enable_caching=self.config.enable_caching
        )
    
    def _generate_cache_key(self, symbol: str, timeframe: TimeFrame, 
                          start_date: datetime, end_date: datetime) -> str:
        """Generate unique cache key for data request."""
        key_data = f"{symbol}_{timeframe.value}_{start_date.isoformat()}_{end_date.isoformat()}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get cache file path for given cache key."""
        if self.config.cache_compression:
            return self.config.cache_directory / f"{cache_key}.parquet"
        else:
            return self.config.cache_directory / f"{cache_key}.csv"
    
    async def _load_from_cache(self, cache_key: str) -> Optional[List[ProcessedDataPoint]]:
        """Load processed data from cache if available and valid."""
        if not self.config.enable_caching:
            return None
        
        cache_file = self._get_cache_file_path(cache_key)
        metadata_file = self.config.cache_directory / f"{cache_key}_metadata.json"
        
        if not cache_file.exists() or not metadata_file.exists():
            return None
        
        try:
            # Load metadata
            async with aiofiles.open(metadata_file, 'r') as f:
                metadata_dict = json.loads(await f.read())
                metadata = CacheMetadata(**metadata_dict)
            
            # Check cache age
            cache_age = datetime.utcnow() - metadata.cache_created
            if cache_age.total_seconds() > (self.config.max_cache_age_hours * 3600):
                logger.info("Cache expired", cache_key=cache_key, age_hours=cache_age.total_seconds()/3600)
                return None
            
            # Load data
            if self.config.cache_compression:
                df = pd.read_parquet(cache_file)
            else:
                df = pd.read_csv(cache_file, parse_dates=['timestamp'])
            
            # Convert to ProcessedDataPoint objects
            data_points = []
            for _, row in df.iterrows():
                data_point = ProcessedDataPoint(
                    symbol=row['symbol'],
                    timestamp=pd.to_datetime(row['timestamp']),
                    open_price=Decimal(str(row['open_price'])),
                    high_price=Decimal(str(row['high_price'])),
                    low_price=Decimal(str(row['low_price'])),
                    close_price=Decimal(str(row['close_price'])),
                    volume=Decimal(str(row['volume'])),
                    price_change=Decimal(str(row['price_change'])),
                    price_change_pct=Decimal(str(row['price_change_pct'])),
                    volatility=Decimal(str(row['volatility'])),
                    volume_ratio=Decimal(str(row['volume_ratio'])),
                    sma_5=Decimal(str(row['sma_5'])) if pd.notna(row['sma_5']) else None,
                    sma_20=Decimal(str(row['sma_20'])) if pd.notna(row['sma_20']) else None,
                    rsi_14=Decimal(str(row['rsi_14'])) if pd.notna(row['rsi_14']) else None,
                    is_outlier=bool(row['is_outlier']),
                    has_gaps_before=bool(row['has_gaps_before']),
                    interpolated=bool(row['interpolated'])
                )
                data_points.append(data_point)
            
            self._cache_metadata[cache_key] = metadata
            
            logger.info(
                "Data loaded from cache",
                cache_key=cache_key,
                records=len(data_points),
                data_quality=metadata.data_quality.value
            )
            
            return data_points
            
        except Exception as e:
            logger.error("Failed to load from cache", cache_key=cache_key, error=str(e))
            return None
    
    async def _save_to_cache(self, cache_key: str, data_points: List[ProcessedDataPoint],
                           symbol: str, timeframe: TimeFrame,
                           start_date: datetime, end_date: datetime) -> None:
        """Save processed data to cache."""
        if not self.config.enable_caching:
            return
        
        try:
            # Convert to DataFrame
            data_dicts = []
            for point in data_points:
                data_dict = {
                    'symbol': point.symbol,
                    'timestamp': point.timestamp,
                    'open_price': float(point.open_price),
                    'high_price': float(point.high_price),
                    'low_price': float(point.low_price),
                    'close_price': float(point.close_price),
                    'volume': float(point.volume),
                    'price_change': float(point.price_change),
                    'price_change_pct': float(point.price_change_pct),
                    'volatility': float(point.volatility),
                    'volume_ratio': float(point.volume_ratio),
                    'sma_5': float(point.sma_5) if point.sma_5 else None,
                    'sma_20': float(point.sma_20) if point.sma_20 else None,
                    'rsi_14': float(point.rsi_14) if point.rsi_14 else None,
                    'is_outlier': point.is_outlier,
                    'has_gaps_before': point.has_gaps_before,
                    'interpolated': point.interpolated
                }
                data_dicts.append(data_dict)
            
            df = pd.DataFrame(data_dicts)
            
            # Save data
            cache_file = self._get_cache_file_path(cache_key)
            if self.config.cache_compression:
                df.to_parquet(cache_file, index=False)
            else:
                df.to_csv(cache_file, index=False)
            
            # Calculate data quality
            data_quality = self._assess_data_quality(data_points)
            
            # Create metadata
            file_size = cache_file.stat().st_size
            checksum = hashlib.md5(df.to_string().encode()).hexdigest()
            
            metadata = CacheMetadata(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                total_records=len(data_points),
                cache_created=datetime.utcnow(),
                data_quality=data_quality,
                checksum=checksum,
                file_size_bytes=file_size
            )
            
            # Save metadata
            metadata_file = self.config.cache_directory / f"{cache_key}_metadata.json"
            metadata_dict = {
                'symbol': metadata.symbol,
                'timeframe': metadata.timeframe.value,
                'start_date': metadata.start_date.isoformat(),
                'end_date': metadata.end_date.isoformat(),
                'total_records': metadata.total_records,
                'cache_created': metadata.cache_created.isoformat(),
                'data_quality': metadata.data_quality.value,
                'checksum': metadata.checksum,
                'file_size_bytes': metadata.file_size_bytes
            }
            
            async with aiofiles.open(metadata_file, 'w') as f:
                await f.write(json.dumps(metadata_dict, indent=2))
            
            self._cache_metadata[cache_key] = metadata
            
            logger.info(
                "Data saved to cache",
                cache_key=cache_key,
                records=len(data_points),
                file_size_mb=file_size / (1024 * 1024),
                data_quality=data_quality.value
            )
            
        except Exception as e:
            logger.error("Failed to save to cache", cache_key=cache_key, error=str(e))
    
    def _assess_data_quality(self, data_points: List[ProcessedDataPoint]) -> DataQuality:
        """Assess the quality of processed data."""
        if not data_points:
            return DataQuality.POOR
        
        total_points = len(data_points)
        outliers = sum(1 for point in data_points if point.is_outlier)
        gaps = sum(1 for point in data_points if point.has_gaps_before)
        interpolated = sum(1 for point in data_points if point.interpolated)
        
        outlier_ratio = outliers / total_points
        gap_ratio = gaps / total_points
        interpolated_ratio = interpolated / total_points
        
        # Calculate overall quality score
        quality_score = 1.0 - (outlier_ratio * 0.3 + gap_ratio * 0.5 + interpolated_ratio * 0.2)
        
        if quality_score >= 0.99:
            return DataQuality.EXCELLENT
        elif quality_score >= 0.95:
            return DataQuality.GOOD
        elif quality_score >= 0.90:
            return DataQuality.FAIR
        else:
            return DataQuality.POOR
    
    async def process_historical_data(self, symbol: str, timeframe: TimeFrame,
                                    start_date: datetime, end_date: datetime,
                                    force_refresh: bool = False) -> List[ProcessedDataPoint]:
        """Process historical data with caching and standardization.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            timeframe: Data timeframe
            start_date: Start date for data
            end_date: End date for data
            force_refresh: Force refresh from source, ignore cache
            
        Returns:
            List of processed data points
        """
        cache_key = self._generate_cache_key(symbol, timeframe, start_date, end_date)
        
        # Try to load from cache first
        if not force_refresh:
            cached_data = await self._load_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        logger.info(
            "Processing historical data from source",
            symbol=symbol,
            timeframe=timeframe.value,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Load raw data from Binance
        if not self.binance_client:
            raise ValueError("BinanceDataClient required for data processing")
        
        raw_data = await self.binance_client.fetch_historical_klines(
            symbol=symbol,
            timeframe=timeframe.value,
            start_date=start_date,
            end_date=end_date
        )
        
        if not raw_data:
            raise ValueError(f"No data received for {symbol} {timeframe.value}")
        
        # Process raw data
        processed_data = await self._process_raw_data(raw_data, timeframe)
        
        # Validate data quality
        data_quality = self._assess_data_quality(processed_data)
        if data_quality.value not in [q.value for q in [DataQuality.EXCELLENT, DataQuality.GOOD, DataQuality.FAIR]]:
            if self.config.min_data_quality != DataQuality.POOR:
                logger.warning(
                    "Data quality below minimum threshold",
                    symbol=symbol,
                    quality=data_quality.value,
                    min_required=self.config.min_data_quality.value
                )
        
        # Save to cache
        await self._save_to_cache(cache_key, processed_data, symbol, timeframe, start_date, end_date)
        
        return processed_data
    
    async def _process_raw_data(self, raw_data: List[HistoricalDataPoint], 
                              timeframe: TimeFrame) -> List[ProcessedDataPoint]:
        """Process raw historical data points."""
        if not raw_data:
            return []
        
        # Sort by timestamp
        sorted_data = sorted(raw_data, key=lambda x: x.timestamp)
        
        processed_points = []
        
        # Calculate expected interval for gap detection
        interval_minutes = self._get_timeframe_minutes(timeframe)
        expected_interval = timedelta(minutes=interval_minutes)
        
        # Process each data point
        for i, raw_point in enumerate(sorted_data):
            # Calculate price change from previous period
            if i > 0:
                prev_close = sorted_data[i-1].close_price
                price_change = raw_point.close_price - prev_close
                price_change_pct = (price_change / prev_close) * Decimal('100')
                
                # Check for gaps
                time_diff = raw_point.timestamp - sorted_data[i-1].timestamp
                has_gaps_before = time_diff > expected_interval * 1.5
            else:
                price_change = Decimal('0')
                price_change_pct = Decimal('0')
                has_gaps_before = False
            
            # Calculate volatility (high-low range as percentage of close)
            volatility = ((raw_point.high_price - raw_point.low_price) / raw_point.close_price) * Decimal('100')
            
            # Calculate volume ratio (will be updated with moving average later)
            volume_ratio = Decimal('1.0')  # Placeholder
            
            # Create processed point
            processed_point = ProcessedDataPoint(
                symbol=raw_point.symbol,
                timestamp=raw_point.timestamp,
                open_price=raw_point.open_price,
                high_price=raw_point.high_price,
                low_price=raw_point.low_price,
                close_price=raw_point.close_price,
                volume=raw_point.volume,
                price_change=price_change,
                price_change_pct=price_change_pct,
                volatility=volatility,
                volume_ratio=volume_ratio,
                has_gaps_before=has_gaps_before,
                interpolated=False,
                is_outlier=False
            )
            
            processed_points.append(processed_point)
        
        # Calculate technical indicators
        await self._calculate_technical_indicators(processed_points)
        
        # Detect outliers
        if self.config.outlier_detection:
            self._detect_outliers(processed_points)
        
        # Calculate volume ratios
        self._calculate_volume_ratios(processed_points)
        
        return processed_points
    
    def _get_timeframe_minutes(self, timeframe: TimeFrame) -> int:
        """Get timeframe in minutes."""
        timeframe_minutes = {
            TimeFrame.M1: 1,
            TimeFrame.M5: 5,
            TimeFrame.M15: 15,
            TimeFrame.M30: 30,
            TimeFrame.H1: 60,
            TimeFrame.H4: 240,
            TimeFrame.D1: 1440
        }
        return timeframe_minutes.get(timeframe, 60)
    
    async def _calculate_technical_indicators(self, data_points: List[ProcessedDataPoint]) -> None:
        """Calculate basic technical indicators."""
        if len(data_points) < 20:
            return
        
        # Calculate SMAs
        for i in range(len(data_points)):
            # SMA 5
            if i >= 4:
                sma_5_sum = sum(data_points[j].close_price for j in range(i-4, i+1))
                data_points[i].sma_5 = sma_5_sum / Decimal('5')
            
            # SMA 20
            if i >= 19:
                sma_20_sum = sum(data_points[j].close_price for j in range(i-19, i+1))
                data_points[i].sma_20 = sma_20_sum / Decimal('20')
            
            # RSI 14
            if i >= 14:
                data_points[i].rsi_14 = self._calculate_rsi(data_points, i, 14)
    
    def _calculate_rsi(self, data_points: List[ProcessedDataPoint], index: int, period: int) -> Decimal:
        """Calculate RSI for given index and period."""
        if index < period:
            return Decimal('50')  # Neutral RSI
        
        gains = []
        losses = []
        
        for i in range(index - period + 1, index + 1):
            change = data_points[i].price_change
            if change > 0:
                gains.append(change)
                losses.append(Decimal('0'))
            else:
                gains.append(Decimal('0'))
                losses.append(-change)
        
        avg_gain = sum(gains) / Decimal(str(period))
        avg_loss = sum(losses) / Decimal(str(period))
        
        if avg_loss == 0:
            return Decimal('100')
        
        rs = avg_gain / avg_loss
        rsi = Decimal('100') - (Decimal('100') / (Decimal('1') + rs))
        
        return rsi
    
    def _detect_outliers(self, data_points: List[ProcessedDataPoint]) -> None:
        """Detect and flag outliers in the data."""
        if len(data_points) < 10:
            return
        
        # Calculate statistics for price changes
        price_changes = [float(point.price_change_pct) for point in data_points]
        mean_change = np.mean(price_changes)
        std_change = np.std(price_changes)
        
        # Flag outliers based on standard deviation
        threshold = self.config.outlier_threshold_std
        for i, point in enumerate(data_points):
            change_pct = float(point.price_change_pct)
            if abs(change_pct - mean_change) > (threshold * std_change):
                point.is_outlier = True
    
    def _calculate_volume_ratios(self, data_points: List[ProcessedDataPoint]) -> None:
        """Calculate volume ratios against moving average."""
        if len(data_points) < 20:
            return
        
        # Calculate 20-period volume moving average
        for i in range(19, len(data_points)):
            avg_volume = sum(data_points[j].volume for j in range(i-19, i+1)) / Decimal('20')
            if avg_volume > 0:
                data_points[i].volume_ratio = data_points[i].volume / avg_volume
    
    async def get_multi_timeframe_data(self, symbol: str, 
                                     timeframes: List[TimeFrame],
                                     start_date: datetime, 
                                     end_date: datetime) -> Dict[TimeFrame, List[ProcessedDataPoint]]:
        """Get processed data for multiple timeframes.
        
        Args:
            symbol: Trading symbol
            timeframes: List of timeframes to process
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary mapping timeframes to processed data
        """
        results = {}
        
        # Process timeframes in parallel if enabled
        if self.config.parallel_processing:
            tasks = []
            for timeframe in timeframes:
                task = self.process_historical_data(symbol, timeframe, start_date, end_date)
                tasks.append((timeframe, task))
            
            # Execute tasks
            for timeframe, task in tasks:
                try:
                    data = await task
                    results[timeframe] = data
                    logger.info(
                        "Processed timeframe data",
                        symbol=symbol,
                        timeframe=timeframe.value,
                        records=len(data)
                    )
                except Exception as e:
                    logger.error(
                        "Failed to process timeframe",
                        symbol=symbol,
                        timeframe=timeframe.value,
                        error=str(e)
                    )
        else:
            # Process sequentially
            for timeframe in timeframes:
                try:
                    data = await self.process_historical_data(symbol, timeframe, start_date, end_date)
                    results[timeframe] = data
                except Exception as e:
                    logger.error(
                        "Failed to process timeframe",
                        symbol=symbol,
                        timeframe=timeframe.value,
                        error=str(e)
                    )
        
        return results
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache usage statistics."""
        if not self.config.enable_caching:
            return {"caching_enabled": False}
        
        cache_files = list(self.config.cache_directory.glob("*.parquet")) + \
                     list(self.config.cache_directory.glob("*.csv"))
        
        total_size = sum(f.stat().st_size for f in cache_files)
        
        quality_distribution = {}
        for metadata in self._cache_metadata.values():
            quality = metadata.data_quality.value
            quality_distribution[quality] = quality_distribution.get(quality, 0) + 1
        
        return {
            "caching_enabled": True,
            "cache_directory": str(self.config.cache_directory),
            "total_cache_files": len(cache_files),
            "total_cache_size_mb": total_size / (1024 * 1024),
            "cached_datasets": len(self._cache_metadata),
            "data_quality_distribution": quality_distribution,
            "compression_enabled": self.config.cache_compression
        }
    
    async def clear_cache(self, older_than_hours: Optional[int] = None) -> int:
        """Clear cache files.
        
        Args:
            older_than_hours: Only clear files older than this many hours
            
        Returns:
            Number of files cleared
        """
        if not self.config.enable_caching:
            return 0
        
        files_cleared = 0
        cutoff_time = None
        
        if older_than_hours is not None:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        # Clear cache files
        for cache_file in self.config.cache_directory.iterdir():
            if cache_file.is_file():
                if cutoff_time is None or datetime.fromtimestamp(cache_file.stat().st_mtime) < cutoff_time:
                    cache_file.unlink()
                    files_cleared += 1
        
        # Clear metadata
        if cutoff_time is None:
            self._cache_metadata.clear()
        else:
            keys_to_remove = [
                key for key, metadata in self._cache_metadata.items()
                if metadata.cache_created < cutoff_time
            ]
            for key in keys_to_remove:
                del self._cache_metadata[key]
        
        logger.info("Cache cleared", files_cleared=files_cleared, older_than_hours=older_than_hours)
        
        return files_cleared