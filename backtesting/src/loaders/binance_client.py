"""Binance API client for historical data fetching.

This module provides functionality to fetch historical market data from Binance
using their REST API for backtesting purposes.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pathlib import Path

import aiohttp
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

from ..models.backtest_result import BacktestResult
from .data_loader import HistoricalDataPoint
from .binance_data_downloader import BinanceDataDownloader, DownloadConfig


class BinanceDataClient:
    """Binance API client for fetching historical market data."""

    def __init__(self, 
                 api_key: Optional[str] = None, 
                 api_secret: Optional[str] = None,
                 data_dir: str = "./data/binance",
                 prefer_offline: bool = True):
        """
        Initialize Binance client.
        
        Args:
            api_key: Binance API key (optional for public data)
            api_secret: Binance API secret (optional for public data)
            data_dir: Directory for offline data storage
            prefer_offline: Whether to prefer offline data over API calls
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.data_dir = Path(data_dir)
        self.prefer_offline = prefer_offline
        self.client = None
        if api_key and api_secret:
            self.client = Client(api_key, api_secret)
        else:
            self.client = Client()  # Public client for historical data
        
        # Initialize downloader for offline data
        download_config = DownloadConfig(data_dir=str(self.data_dir))
        self.downloader = BinanceDataDownloader(download_config)
        
        # Binance timeframe mapping
        self.timeframe_mapping = {
            "1m": Client.KLINE_INTERVAL_1MINUTE,
            "3m": Client.KLINE_INTERVAL_3MINUTE,
            "5m": Client.KLINE_INTERVAL_5MINUTE,
            "15m": Client.KLINE_INTERVAL_15MINUTE,
            "30m": Client.KLINE_INTERVAL_30MINUTE,
            "1h": Client.KLINE_INTERVAL_1HOUR,
            "2h": Client.KLINE_INTERVAL_2HOUR,
            "4h": Client.KLINE_INTERVAL_4HOUR,
            "6h": Client.KLINE_INTERVAL_6HOUR,
            "8h": Client.KLINE_INTERVAL_8HOUR,
            "12h": Client.KLINE_INTERVAL_12HOUR,
            "1d": Client.KLINE_INTERVAL_1DAY,
            "3d": Client.KLINE_INTERVAL_3DAY,
            "1w": Client.KLINE_INTERVAL_1WEEK,
            "1M": Client.KLINE_INTERVAL_1MONTH
        }

    async def fetch_historical_klines(self, 
                                    symbol: str,
                                    timeframe: str,
                                    start_date: datetime,
                                    end_date: datetime,
                                    limit: int = 1000) -> List[HistoricalDataPoint]:
        """
        Fetch historical kline data from Binance.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            timeframe: Timeframe for klines (e.g., '1h', '1d')
            start_date: Start date for data
            end_date: End date for data
            limit: Maximum number of klines per request (max 1000)
            
        Returns:
            List of HistoricalDataPoint objects
            
        Raises:
            ValueError: If timeframe is not supported
            BinanceAPIException: If API request fails
        """
        if timeframe not in self.timeframe_mapping:
            raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {list(self.timeframe_mapping.keys())}")
        
        interval = self.timeframe_mapping[timeframe]
        data_points = []
        
        # Convert dates to milliseconds
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)
        
        current_start = start_ms
        
        try:
            while current_start < end_ms:
                # Fetch klines in batches
                klines = await self._fetch_klines_batch(
                    symbol=symbol,
                    interval=interval,
                    start_time=current_start,
                    end_time=end_ms,
                    limit=limit
                )
                
                if not klines:
                    break
                
                # Convert klines to HistoricalDataPoint objects
                for kline in klines:
                    data_point = self._convert_kline_to_datapoint(symbol, kline)
                    data_points.append(data_point)
                
                # Update start time for next batch
                last_kline_time = int(klines[-1][6])  # Close time
                current_start = last_kline_time + 1
                
                # Add small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
        except (BinanceAPIException, BinanceRequestException) as e:
            raise Exception(f"Binance API error: {str(e)}")
        
        return data_points

    async def _fetch_klines_batch(self,
                                symbol: str,
                                interval: str,
                                start_time: int,
                                end_time: int,
                                limit: int) -> List[List[Any]]:
        """
        Fetch a single batch of klines from Binance API.
        
        Args:
            symbol: Trading pair symbol
            interval: Binance interval constant
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            limit: Maximum number of klines
            
        Returns:
            List of kline data arrays
        """
        # Use asyncio to run the synchronous client call
        loop = asyncio.get_event_loop()
        
        klines = await loop.run_in_executor(
            None,
            lambda: self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_time,
                end_str=end_time,
                limit=limit
            )
        )
        
        return klines

    def _convert_kline_to_datapoint(self, symbol: str, kline: List[Any]) -> HistoricalDataPoint:
        """
        Convert Binance kline data to HistoricalDataPoint.
        
        Binance kline format:
        [
            1499040000000,      # Open time
            "0.01634790",       # Open
            "0.80000000",       # High
            "0.01575800",       # Low
            "0.01577100",       # Close
            "148976.11427815",  # Volume
            1499644799999,      # Close time
            "2434.19055334",    # Quote asset volume
            308,                # Number of trades
            "1756.87402397",    # Taker buy base asset volume
            "28.46694368",      # Taker buy quote asset volume
            "17928899.62484339" # Ignore
        ]
        
        Args:
            symbol: Trading pair symbol
            kline: Binance kline data array
            
        Returns:
            HistoricalDataPoint object
        """
        # Convert timestamp from milliseconds to datetime
        timestamp = datetime.fromtimestamp(int(kline[0]) / 1000)
        
        return HistoricalDataPoint(
            symbol=symbol,
            timestamp=timestamp,
            open_price=Decimal(str(kline[1])),
            high_price=Decimal(str(kline[2])),
            low_price=Decimal(str(kline[3])),
            close_price=Decimal(str(kline[4])),
            volume=Decimal(str(kline[5])),
            quote_volume=Decimal(str(kline[7])),
            trade_count=int(kline[8])
        )

    async def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange information including available symbols.
        
        Returns:
            Dictionary containing exchange information
        """
        loop = asyncio.get_event_loop()
        
        try:
            exchange_info = await loop.run_in_executor(
                None,
                self.client.get_exchange_info
            )
            return exchange_info
        except (BinanceAPIException, BinanceRequestException) as e:
            raise Exception(f"Failed to get exchange info: {str(e)}")

    async def get_available_symbols(self) -> List[str]:
        """
        Get list of available trading symbols.
        
        Returns:
            List of symbol strings
        """
        exchange_info = await self.get_exchange_info()
        symbols = []
        
        for symbol_info in exchange_info.get('symbols', []):
            if symbol_info.get('status') == 'TRADING':
                symbols.append(symbol_info['symbol'])
        
        return symbols

    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol exists on Binance.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            True if symbol exists and is trading
        """
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return ticker is not None
        except (BinanceAPIException, BinanceRequestException):
            return False

    def get_supported_timeframes(self) -> List[str]:
        """
        Get list of supported timeframes.
        
        Returns:
            List of supported timeframe strings
        """
        return list(self.timeframe_mapping.keys())
    
    async def fetch_historical_data_hybrid(self,
                                          symbol: str,
                                          timeframe: str,
                                          start_date: datetime,
                                          end_date: datetime) -> List[HistoricalDataPoint]:
        """
        Fetch historical data using hybrid approach (offline + API).
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            timeframe: Timeframe for klines (e.g., '1m', '1h')
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            List of HistoricalDataPoint objects
        """
        all_data = []
        
        if self.prefer_offline:
            # Try to load from offline data first
            offline_data = await self._load_offline_data(symbol, timeframe, start_date, end_date)
            if offline_data:
                all_data.extend(offline_data)
                
                # Check if we have complete data
                if self._is_data_complete(offline_data, start_date, end_date, timeframe):
                    return sorted(all_data, key=lambda x: x.timestamp)
        
        # Fill gaps with API data
        missing_ranges = self._find_missing_ranges(all_data, start_date, end_date, timeframe)
        
        for missing_start, missing_end in missing_ranges:
            api_data = await self.fetch_historical_klines(
                symbol=symbol,
                timeframe=timeframe,
                start_date=missing_start,
                end_date=missing_end
            )
            all_data.extend(api_data)
        
        return sorted(all_data, key=lambda x: x.timestamp)
    
    async def _load_offline_data(self,
                               symbol: str,
                               timeframe: str,
                               start_date: datetime,
                               end_date: datetime) -> List[HistoricalDataPoint]:
        """
        Load data from offline CSV files.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe for data
            start_date: Start date
            end_date: End date
            
        Returns:
            List of HistoricalDataPoint objects from offline data
        """
        data_points = []
        
        # Look for CSV files in the data directory
        pattern = f"{symbol}-{timeframe}-*.csv"
        csv_files = list(self.data_dir.glob(f"**/{pattern}"))
        
        for csv_file in csv_files:
            try:
                df = self.downloader.load_csv_data(csv_file)
                
                # Filter data by date range
                mask = (df['open_time'] >= start_date) & (df['open_time'] <= end_date)
                filtered_df = df[mask]
                
                # Convert to HistoricalDataPoint objects
                for _, row in filtered_df.iterrows():
                    data_point = HistoricalDataPoint(
                        symbol=symbol,
                        timestamp=row['open_time'],
                        open_price=Decimal(str(row['open'])),
                        high_price=Decimal(str(row['high'])),
                        low_price=Decimal(str(row['low'])),
                        close_price=Decimal(str(row['close'])),
                        volume=Decimal(str(row['volume'])),
                        quote_volume=Decimal(str(row['quote_asset_volume'])),
                        trade_count=int(row['number_of_trades'])
                    )
                    data_points.append(data_point)
                    
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
                continue
        
        return data_points
    
    def _is_data_complete(self,
                         data: List[HistoricalDataPoint],
                         start_date: datetime,
                         end_date: datetime,
                         timeframe: str) -> bool:
        """
        Check if the data covers the complete requested range.
        
        Args:
            data: List of data points
            start_date: Requested start date
            end_date: Requested end date
            timeframe: Data timeframe
            
        Returns:
            True if data is complete
        """
        if not data:
            return False
        
        # Sort data by timestamp
        sorted_data = sorted(data, key=lambda x: x.timestamp)
        
        # Check if we have data covering the full range
        data_start = sorted_data[0].timestamp
        data_end = sorted_data[-1].timestamp
        
        # Allow some tolerance for start/end times
        tolerance = timedelta(minutes=1)
        
        return (data_start <= start_date + tolerance and 
                data_end >= end_date - tolerance)
    
    def _find_missing_ranges(self,
                           data: List[HistoricalDataPoint],
                           start_date: datetime,
                           end_date: datetime,
                           timeframe: str) -> List[tuple]:
        """
        Find missing date ranges in the data.
        
        Args:
            data: Existing data points
            start_date: Requested start date
            end_date: Requested end date
            timeframe: Data timeframe
            
        Returns:
            List of (start, end) tuples for missing ranges
        """
        if not data:
            return [(start_date, end_date)]
        
        # Sort data by timestamp
        sorted_data = sorted(data, key=lambda x: x.timestamp)
        
        missing_ranges = []
        
        # Check if we need data before the first point
        if sorted_data[0].timestamp > start_date:
            missing_ranges.append((start_date, sorted_data[0].timestamp))
        
        # Check if we need data after the last point
        if sorted_data[-1].timestamp < end_date:
            missing_ranges.append((sorted_data[-1].timestamp, end_date))
        
        return missing_ranges
    
    async def download_and_prepare_data(self,
                                      symbols: List[str],
                                      timeframe: str,
                                      start_date: str,
                                      end_date: str) -> Dict[str, List[Path]]:
        """
        Download and prepare offline data for multiple symbols.
        
        Args:
            symbols: List of trading pair symbols
            timeframe: Timeframe for data (e.g., '1m', '1h')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            Dictionary mapping symbols to their downloaded file paths
        """
        # Update downloader config for the specified timeframe
        self.downloader.config.interval = timeframe
        
        # Download data for all symbols
        results = self.downloader.download_multiple_symbols(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date
        )
        
        return results