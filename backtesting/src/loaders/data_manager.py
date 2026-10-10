"""Data management tool for Binance historical data."""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

from .binance_client import BinanceDataClient
from .binance_data_downloader import BinanceDataDownloader, DownloadConfig
from .data_loader import HistoricalDataPoint


class DataManager:
    """Manages historical data with automatic gap detection and filling."""
    
    def __init__(self, 
                 data_dir: str = "./data/binance",
                 api_key: Optional[str] = None,
                 api_secret: Optional[str] = None):
        """
        Initialize data manager.
        
        Args:
            data_dir: Directory for data storage
            api_key: Binance API key (optional)
            api_secret: Binance API secret (optional)
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.client = BinanceDataClient(
            api_key=api_key,
            api_secret=api_secret,
            data_dir=str(self.data_dir),
            prefer_offline=True
        )
        
        download_config = DownloadConfig(data_dir=str(self.data_dir))
        self.downloader = BinanceDataDownloader(download_config)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    async def ensure_data_availability(self,
                                     symbols: List[str],
                                     timeframe: str,
                                     start_date: datetime,
                                     end_date: datetime,
                                     auto_download: bool = True) -> Dict[str, bool]:
        """
        Ensure data availability for given symbols and date range.
        
        Args:
            symbols: List of trading pair symbols
            timeframe: Data timeframe (e.g., '1m', '1h')
            start_date: Start date for data
            end_date: End date for data
            auto_download: Whether to automatically download missing data
            
        Returns:
            Dictionary mapping symbols to availability status
        """
        results = {}
        
        for symbol in symbols:
            try:
                # Check data availability
                is_available = await self._check_data_availability(
                    symbol, timeframe, start_date, end_date
                )
                
                if not is_available and auto_download:
                    self.logger.info(f"Downloading missing data for {symbol}")
                    await self._download_missing_data(
                        symbol, timeframe, start_date, end_date
                    )
                    # Re-check availability after download
                    is_available = await self._check_data_availability(
                        symbol, timeframe, start_date, end_date
                    )
                
                results[symbol] = is_available
                
            except Exception as e:
                self.logger.error(f"Error ensuring data for {symbol}: {e}")
                results[symbol] = False
        
        return results
    
    async def get_data_gaps(self,
                          symbol: str,
                          timeframe: str,
                          start_date: datetime,
                          end_date: datetime) -> List[Tuple[datetime, datetime]]:
        """
        Identify gaps in historical data.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Data timeframe
            start_date: Start date to check
            end_date: End date to check
            
        Returns:
            List of (gap_start, gap_end) tuples
        """
        try:
            # Load existing offline data
            offline_data = await self.client._load_offline_data(
                symbol, timeframe, start_date, end_date
            )
            
            if not offline_data:
                return [(start_date, end_date)]
            
            # Sort data by timestamp
            sorted_data = sorted(offline_data, key=lambda x: x.timestamp)
            
            gaps = []
            expected_interval = self._get_interval_timedelta(timeframe)
            
            # Check for gap at the beginning
            if sorted_data[0].timestamp > start_date:
                gaps.append((start_date, sorted_data[0].timestamp))
            
            # Check for gaps between data points
            for i in range(len(sorted_data) - 1):
                current_time = sorted_data[i].timestamp
                next_time = sorted_data[i + 1].timestamp
                expected_next = current_time + expected_interval
                
                # Allow some tolerance for timing differences
                tolerance = timedelta(seconds=30)
                if next_time > expected_next + tolerance:
                    gaps.append((current_time + expected_interval, next_time))
            
            # Check for gap at the end
            if sorted_data[-1].timestamp < end_date:
                gaps.append((sorted_data[-1].timestamp + expected_interval, end_date))
            
            return gaps
            
        except Exception as e:
            self.logger.error(f"Error detecting gaps for {symbol}: {e}")
            return [(start_date, end_date)]
    
    async def fill_data_gaps(self,
                           symbol: str,
                           timeframe: str,
                           gaps: List[Tuple[datetime, datetime]]) -> bool:
        """
        Fill identified data gaps using API calls.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Data timeframe
            gaps: List of (gap_start, gap_end) tuples
            
        Returns:
            True if all gaps were successfully filled
        """
        success = True
        
        for gap_start, gap_end in gaps:
            try:
                self.logger.info(f"Filling gap for {symbol} from {gap_start} to {gap_end}")
                
                # Fetch data from API
                gap_data = await self.client.fetch_historical_klines(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=gap_start,
                    end_date=gap_end
                )
                
                if gap_data:
                    # Save gap data to CSV
                    await self._save_gap_data_to_csv(symbol, timeframe, gap_data)
                    self.logger.info(f"Successfully filled gap with {len(gap_data)} data points")
                else:
                    self.logger.warning(f"No data received for gap {gap_start} to {gap_end}")
                    success = False
                    
            except Exception as e:
                self.logger.error(f"Error filling gap for {symbol}: {e}")
                success = False
        
        return success
    
    async def update_latest_data(self,
                               symbols: List[str],
                               timeframe: str,
                               lookback_hours: int = 24) -> Dict[str, int]:
        """
        Update with the latest data from API.
        
        Args:
            symbols: List of trading pair symbols
            timeframe: Data timeframe
            lookback_hours: Hours to look back for updates
            
        Returns:
            Dictionary mapping symbols to number of new data points added
        """
        results = {}
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=lookback_hours)
        
        for symbol in symbols:
            try:
                # Fetch latest data
                latest_data = await self.client.fetch_historical_klines(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_time,
                    end_date=end_time
                )
                
                if latest_data:
                    # Save to CSV
                    await self._save_gap_data_to_csv(symbol, timeframe, latest_data)
                    results[symbol] = len(latest_data)
                    self.logger.info(f"Updated {symbol} with {len(latest_data)} new data points")
                else:
                    results[symbol] = 0
                    
            except Exception as e:
                self.logger.error(f"Error updating latest data for {symbol}: {e}")
                results[symbol] = 0
        
        return results
    
    async def _check_data_availability(self,
                                     symbol: str,
                                     timeframe: str,
                                     start_date: datetime,
                                     end_date: datetime) -> bool:
        """
        Check if data is available for the given parameters.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Data timeframe
            start_date: Start date
            end_date: End date
            
        Returns:
            True if data is available and complete
        """
        try:
            offline_data = await self.client._load_offline_data(
                symbol, timeframe, start_date, end_date
            )
            
            return self.client._is_data_complete(
                offline_data, start_date, end_date, timeframe
            )
            
        except Exception as e:
            self.logger.error(f"Error checking data availability: {e}")
            return False
    
    async def _download_missing_data(self,
                                   symbol: str,
                                   timeframe: str,
                                   start_date: datetime,
                                   end_date: datetime) -> bool:
        """
        Download missing data from Binance data vision.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Data timeframe
            start_date: Start date
            end_date: End date
            
        Returns:
            True if download was successful
        """
        try:
            # Update downloader config
            self.downloader.config.interval = timeframe
            
            # Format dates for downloader
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # Download data
            results = self.downloader.download_multiple_symbols(
                symbols=[symbol],
                start_date=start_str,
                end_date=end_str
            )
            
            return symbol in results and len(results[symbol]) > 0
            
        except Exception as e:
            self.logger.error(f"Error downloading data: {e}")
            return False
    
    async def _save_gap_data_to_csv(self,
                                  symbol: str,
                                  timeframe: str,
                                  data: List[HistoricalDataPoint]) -> None:
        """
        Save gap data to CSV file.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Data timeframe
            data: List of data points to save
        """
        if not data:
            return
        
        # Create filename based on date range
        start_date = min(data, key=lambda x: x.timestamp).timestamp
        end_date = max(data, key=lambda x: x.timestamp).timestamp
        
        filename = f"{symbol}-{timeframe}-{start_date.strftime('%Y-%m-%d')}-{end_date.strftime('%Y-%m-%d')}-gap.csv"
        filepath = self.data_dir / "gaps" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to CSV format
        csv_data = []
        for point in data:
            csv_data.append([
                int(point.timestamp.timestamp() * 1000),  # open_time
                str(point.open_price),
                str(point.high_price),
                str(point.low_price),
                str(point.close_price),
                str(point.volume),
                int((point.timestamp + timedelta(minutes=1)).timestamp() * 1000),  # close_time
                str(point.quote_volume),
                point.trade_count,
                "0",  # taker_buy_base_asset_volume
                "0",  # taker_buy_quote_asset_volume
                "0"   # ignore
            ])
        
        # Write to CSV
        import csv
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
        
        self.logger.info(f"Saved {len(data)} gap data points to {filepath}")
    
    def _get_interval_timedelta(self, timeframe: str) -> timedelta:
        """
        Convert timeframe string to timedelta.
        
        Args:
            timeframe: Timeframe string (e.g., '1m', '1h')
            
        Returns:
            Corresponding timedelta object
        """
        interval_map = {
            '1m': timedelta(minutes=1),
            '3m': timedelta(minutes=3),
            '5m': timedelta(minutes=5),
            '15m': timedelta(minutes=15),
            '30m': timedelta(minutes=30),
            '1h': timedelta(hours=1),
            '2h': timedelta(hours=2),
            '4h': timedelta(hours=4),
            '6h': timedelta(hours=6),
            '8h': timedelta(hours=8),
            '12h': timedelta(hours=12),
            '1d': timedelta(days=1),
            '3d': timedelta(days=3),
            '1w': timedelta(weeks=1),
            '1M': timedelta(days=30)  # Approximate
        }
        
        return interval_map.get(timeframe, timedelta(minutes=1))
    
    def get_data_summary(self, symbol: str, timeframe: str) -> Dict:
        """
        Get summary of available data for a symbol.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Data timeframe
            
        Returns:
            Dictionary with data summary information
        """
        try:
            # Find all CSV files for this symbol and timeframe
            pattern = f"{symbol}-{timeframe}-*.csv"
            csv_files = list(self.data_dir.glob(f"**/{pattern}"))
            
            if not csv_files:
                return {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'files_count': 0,
                    'date_range': None,
                    'total_records': 0
                }
            
            # Analyze files
            earliest_date = None
            latest_date = None
            total_records = 0
            
            for csv_file in csv_files:
                try:
                    df = self.downloader.load_csv_data(csv_file)
                    if not df.empty:
                        file_start = df['open_time'].min()
                        file_end = df['open_time'].max()
                        
                        if earliest_date is None or file_start < earliest_date:
                            earliest_date = file_start
                        if latest_date is None or file_end > latest_date:
                            latest_date = file_end
                        
                        total_records += len(df)
                        
                except Exception as e:
                    self.logger.warning(f"Error reading {csv_file}: {e}")
                    continue
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'files_count': len(csv_files),
                'date_range': (earliest_date, latest_date) if earliest_date else None,
                'total_records': total_records
            }
            
        except Exception as e:
            self.logger.error(f"Error getting data summary: {e}")
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'files_count': 0,
                'date_range': None,
                'total_records': 0,
                'error': str(e)
            }