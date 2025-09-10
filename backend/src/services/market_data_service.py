from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Any, Callable
from uuid import UUID
import logging
import asyncio

from ..models.market_data import MarketData
from ..lib.data_ingestion.data_ingester import DataIngester


class MarketDataService:
    def __init__(self, max_workers: int = 4):
        self.data_ingester = DataIngester(max_workers)
        self.logger = logging.getLogger(__name__)
        self._real_time_subscriptions: Dict[str, List[Callable]] = {}
        self._data_cache: Dict[str, List[MarketData]] = {}
        self._cache_expiry: Dict[str, datetime] = {}

    def get_current_market_data(
        self,
        symbols: List[str],
        timeframe: str = "1m",
        limit: int = 100
    ) -> Dict[str, List[MarketData]]:
        """Get current market data for specified symbols"""
        
        self.logger.info(f"Fetching current market data for {len(symbols)} symbols")
        
        try:
            # Check cache first
            cached_data = {}
            symbols_to_fetch = []
            
            for symbol in symbols:
                cache_key = f"{symbol}_{timeframe}_{limit}"
                if self._is_cache_valid(cache_key):
                    cached_data[symbol] = self._data_cache[cache_key]
                    self.logger.debug(f"Using cached data for {symbol}")
                else:
                    symbols_to_fetch.append(symbol)
            
            # Fetch fresh data for symbols not in cache
            fresh_data = {}
            if symbols_to_fetch:
                self.logger.info(f"Fetching fresh data for {len(symbols_to_fetch)} symbols")
                
                # Use batch ingestion with retry
                fresh_data = self.data_ingester.batch_ingest_with_retry(
                    symbols=symbols_to_fetch,
                    max_retries=3,
                    retry_delay=2
                )
                
                # Update cache
                for symbol, data in fresh_data.items():
                    if data:
                        cache_key = f"{symbol}_{timeframe}_{limit}"
                        self._data_cache[cache_key] = data
                        self._cache_expiry[cache_key] = datetime.utcnow() + timedelta(minutes=1)
            
            # Combine cached and fresh data
            result = {**cached_data, **fresh_data}
            
            self.logger.info(f"Retrieved market data for {len(result)} symbols")
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching current market data: {e}")
            return {}

    def get_historical_market_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1m"
    ) -> List[MarketData]:
        """Get historical market data for a specific symbol and date range"""
        
        self.logger.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
        
        try:
            historical_data = self.data_ingester.ingest_historical_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe
            )
            
            self.logger.info(f"Retrieved {len(historical_data)} historical records for {symbol}")
            return historical_data
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return []

    def get_market_data_by_id(self, data_id: UUID) -> Optional[MarketData]:
        """Get specific market data record by ID"""
        
        # This would typically query from database
        # For now, return None as placeholder
        self.logger.info(f"Retrieving market data by ID: {data_id}")
        return None

    def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get the latest price information for a symbol"""
        
        try:
            # Get recent data
            market_data = self.get_current_market_data([symbol], limit=1)
            
            if symbol not in market_data or not market_data[symbol]:
                self.logger.warning(f"No current data available for {symbol}")
                return None
            
            latest_data = market_data[symbol][0]  # Most recent record
            
            price_info = {
                "symbol": symbol,
                "timestamp": latest_data.timestamp,
                "price": float(latest_data.close_price),
                "open": float(latest_data.open_price),
                "high": float(latest_data.high_price),
                "low": float(latest_data.low_price),
                "volume": float(latest_data.volume),
                "quote_volume": float(latest_data.quote_volume),
                "trade_count": latest_data.trade_count,
                "source": latest_data.source
            }
            
            self.logger.debug(f"Latest price for {symbol}: {price_info['price']}")
            return price_info
            
        except Exception as e:
            self.logger.error(f"Error getting latest price for {symbol}: {e}")
            return None

    def get_price_statistics(
        self,
        symbols: List[str],
        timeframe: str = "1m",
        period_hours: int = 24
    ) -> Dict[str, Dict[str, Any]]:
        """Get price statistics for symbols over a specified period"""
        
        self.logger.info(f"Calculating price statistics for {len(symbols)} symbols over {period_hours}h")
        
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=period_hours)
            
            statistics = {}
            
            for symbol in symbols:
                try:
                    # Get historical data for the period
                    historical_data = self.get_historical_market_data(
                        symbol=symbol,
                        start_date=start_time,
                        end_date=end_time,
                        timeframe=timeframe
                    )
                    
                    if not historical_data:
                        self.logger.warning(f"No historical data for {symbol}")
                        continue
                    
                    # Calculate statistics
                    prices = [float(data.close_price) for data in historical_data]
                    volumes = [float(data.volume) for data in historical_data]
                    
                    if prices:
                        statistics[symbol] = {
                            "min_price": min(prices),
                            "max_price": max(prices),
                            "avg_price": sum(prices) / len(prices),
                            "current_price": prices[-1],
                            "price_change": prices[-1] - prices[0] if len(prices) > 1 else 0,
                            "price_change_percent": ((prices[-1] - prices[0]) / prices[0] * 100) if len(prices) > 1 and prices[0] > 0 else 0,
                            "total_volume": sum(volumes),
                            "avg_volume": sum(volumes) / len(volumes) if volumes else 0,
                            "volatility": self._calculate_volatility(prices),
                            "data_points": len(historical_data),
                            "period_start": start_time,
                            "period_end": end_time
                        }
                        
                except Exception as e:
                    self.logger.error(f"Error calculating statistics for {symbol}: {e}")
                    continue
            
            self.logger.info(f"Calculated statistics for {len(statistics)} symbols")
            return statistics
            
        except Exception as e:
            self.logger.error(f"Error calculating price statistics: {e}")
            return {}

    def start_real_time_stream(
        self,
        symbols: List[str],
        callback: Callable[[MarketData], None]
    ) -> str:
        """Start real-time market data stream for symbols"""
        
        stream_id = f"stream_{datetime.utcnow().timestamp()}"
        
        try:
            self.logger.info(f"Starting real-time stream {stream_id} for {len(symbols)} symbols")
            
            # Register callbacks for symbols
            for symbol in symbols:
                if symbol not in self._real_time_subscriptions:
                    self._real_time_subscriptions[symbol] = []
                self._real_time_subscriptions[symbol].append(callback)
            
            # Start real-time data ingestion
            def stream_callback(market_data: MarketData):
                try:
                    # Call registered callbacks
                    if market_data.symbol in self._real_time_subscriptions:
                        for cb in self._real_time_subscriptions[market_data.symbol]:
                            cb(market_data)
                            
                    # Update cache with real-time data
                    self._update_real_time_cache(market_data)
                    
                except Exception as e:
                    self.logger.error(f"Error in stream callback: {e}")
            
            self.data_ingester.ingest_real_time_data(symbols, stream_callback)
            
            self.logger.info(f"Real-time stream {stream_id} started successfully")
            return stream_id
            
        except Exception as e:
            self.logger.error(f"Error starting real-time stream: {e}")
            return ""

    def stop_real_time_stream(self, stream_id: str, symbols: Optional[List[str]] = None) -> bool:
        """Stop real-time market data stream"""
        
        try:
            self.logger.info(f"Stopping real-time stream {stream_id}")
            
            # Remove callbacks (simplified implementation)
            if symbols:
                for symbol in symbols:
                    if symbol in self._real_time_subscriptions:
                        # In a full implementation, we'd track callbacks by stream_id
                        # For now, clear all callbacks for the symbol
                        self._real_time_subscriptions[symbol] = []
            else:
                # Stop all streams
                self._real_time_subscriptions.clear()
            
            self.logger.info(f"Real-time stream {stream_id} stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping real-time stream: {e}")
            return False

    def validate_market_data_quality(
        self,
        market_data: List[MarketData]
    ) -> Dict[str, Any]:
        """Validate quality of market data"""
        
        try:
            quality_report = self.data_ingester.validate_data_quality(market_data)
            
            self.logger.info(f"Data quality validation completed for {len(market_data)} records")
            return quality_report
            
        except Exception as e:
            self.logger.error(f"Error validating data quality: {e}")
            return {"error": str(e)}

    def get_market_data_statistics(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get ingestion and data statistics"""
        
        try:
            # Get data for analysis
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=1)
            if not end_date:
                end_date = datetime.utcnow()
            
            results = {}
            for symbol in symbols:
                data = self.get_historical_market_data(symbol, start_date, end_date)
                if data:
                    results[symbol] = data
            
            # Generate statistics
            statistics = self.data_ingester.get_ingestion_statistics(results)
            
            self.logger.info(f"Generated statistics for {len(symbols)} symbols")
            return statistics
            
        except Exception as e:
            self.logger.error(f"Error generating market data statistics: {e}")
            return {"error": str(e)}

    def get_supported_symbols(self) -> List[str]:
        """Get list of supported trading symbols"""
        
        # This would typically come from configuration or external API
        supported_symbols = [
            "BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT",
            "BNBUSDT", "SOLUSDT", "MATICUSDT", "AVAXUSDT", "UNIUSDT"
        ]
        
        self.logger.debug(f"Returning {len(supported_symbols)} supported symbols")
        return supported_symbols

    def get_market_status(self) -> Dict[str, Any]:
        """Get overall market status and health metrics"""
        
        try:
            supported_symbols = self.get_supported_symbols()
            sample_symbols = supported_symbols[:5]  # Check first 5 symbols
            
            # Get current data for sample symbols
            current_data = self.get_current_market_data(sample_symbols, limit=1)
            
            active_symbols = len([s for s in sample_symbols if s in current_data and current_data[s]])
            data_freshness = self._check_data_freshness(current_data)
            
            market_status = {
                "timestamp": datetime.utcnow(),
                "total_supported_symbols": len(supported_symbols),
                "active_symbols": active_symbols,
                "inactive_symbols": len(sample_symbols) - active_symbols,
                "data_freshness_minutes": data_freshness,
                "status": "HEALTHY" if active_symbols > len(sample_symbols) * 0.8 else "DEGRADED",
                "real_time_subscriptions": len(self._real_time_subscriptions),
                "cached_symbols": len(self._data_cache)
            }
            
            self.logger.info(f"Market status: {market_status['status']} - {active_symbols}/{len(sample_symbols)} symbols active")
            return market_status
            
        except Exception as e:
            self.logger.error(f"Error getting market status: {e}")
            return {
                "timestamp": datetime.utcnow(),
                "status": "ERROR",
                "error": str(e)
            }

    def clear_cache(self, symbol: Optional[str] = None) -> bool:
        """Clear data cache for specific symbol or all symbols"""
        
        try:
            if symbol:
                # Clear cache for specific symbol
                keys_to_remove = [key for key in self._data_cache.keys() if key.startswith(symbol)]
                for key in keys_to_remove:
                    del self._data_cache[key]
                    if key in self._cache_expiry:
                        del self._cache_expiry[key]
                
                self.logger.info(f"Cleared cache for symbol: {symbol}")
            else:
                # Clear all cache
                self._data_cache.clear()
                self._cache_expiry.clear()
                self.logger.info("Cleared all market data cache")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return False

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is valid and not expired"""
        
        if cache_key not in self._data_cache:
            return False
        
        if cache_key not in self._cache_expiry:
            return False
        
        return datetime.utcnow() < self._cache_expiry[cache_key]

    def _update_real_time_cache(self, market_data: MarketData) -> None:
        """Update cache with real-time market data"""
        
        try:
            symbol = market_data.symbol
            cache_key = f"{symbol}_1m_100"  # Default cache key format
            
            # Initialize cache entry if doesn't exist
            if cache_key not in self._data_cache:
                self._data_cache[cache_key] = []
            
            # Add new data to front of list
            self._data_cache[cache_key].insert(0, market_data)
            
            # Keep only latest 100 records
            if len(self._data_cache[cache_key]) > 100:
                self._data_cache[cache_key] = self._data_cache[cache_key][:100]
            
            # Update expiry
            self._cache_expiry[cache_key] = datetime.utcnow() + timedelta(minutes=1)
            
        except Exception as e:
            self.logger.error(f"Error updating real-time cache: {e}")

    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility"""
        
        if len(prices) < 2:
            return 0.0
        
        try:
            # Calculate returns
            returns = []
            for i in range(1, len(prices)):
                if prices[i-1] > 0:
                    return_pct = (prices[i] - prices[i-1]) / prices[i-1]
                    returns.append(return_pct)
            
            if not returns:
                return 0.0
            
            # Calculate standard deviation of returns
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            volatility = variance ** 0.5
            
            return volatility
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility: {e}")
            return 0.0

    def _check_data_freshness(self, current_data: Dict[str, List[MarketData]]) -> float:
        """Check how fresh the current data is (in minutes)"""
        
        try:
            if not current_data:
                return float('inf')
            
            current_time = datetime.utcnow()
            min_age_minutes = float('inf')
            
            for symbol, data_list in current_data.items():
                if data_list:
                    latest_data = data_list[0]  # Assuming sorted by timestamp desc
                    age_seconds = (current_time - latest_data.timestamp).total_seconds()
                    age_minutes = age_seconds / 60
                    min_age_minutes = min(min_age_minutes, age_minutes)
            
            return min_age_minutes if min_age_minutes != float('inf') else 0.0
            
        except Exception as e:
            self.logger.error(f"Error checking data freshness: {e}")
            return float('inf')