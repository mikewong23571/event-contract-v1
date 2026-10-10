"""Unit tests for Binance data client."""

import asyncio
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock

from src.loaders.binance_client import BinanceDataClient
from src.loaders.data_loader import HistoricalDataPoint, DataSourceConfig, HistoricalDataLoader


class TestBinanceDataClient:
    """Test cases for BinanceDataClient."""

    def setup_method(self):
        """Set up test fixtures."""
        self.client = BinanceDataClient()
        self.test_symbol = "BTCUSDT"
        self.test_timeframe = "1h"
        self.start_date = datetime(2024, 1, 1)
        self.end_date = datetime(2024, 1, 2)

    def test_init_without_credentials(self):
        """Test client initialization without API credentials."""
        client = BinanceDataClient()
        assert client.api_key is None
        assert client.api_secret is None
        assert client.client is not None

    def test_init_with_credentials(self):
        """Test client initialization with API credentials."""
        api_key = "test_key"
        api_secret = "test_secret"
        client = BinanceDataClient(api_key=api_key, api_secret=api_secret)
        assert client.api_key == api_key
        assert client.api_secret == api_secret

    def test_timeframe_mapping(self):
        """Test timeframe mapping contains expected values."""
        expected_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
        for tf in expected_timeframes:
            assert tf in self.client.timeframe_mapping

    def test_get_supported_timeframes(self):
        """Test getting supported timeframes."""
        timeframes = self.client.get_supported_timeframes()
        assert isinstance(timeframes, list)
        assert '1h' in timeframes
        assert '1d' in timeframes

    @patch('src.loaders.binance_client.Client')
    def test_validate_symbol_success(self, mock_client_class):
        """Test successful symbol validation."""
        mock_client = Mock()
        mock_client.get_symbol_ticker.return_value = {'symbol': 'BTCUSDT', 'price': '50000'}
        mock_client_class.return_value = mock_client
        
        client = BinanceDataClient()
        client.client = mock_client
        
        result = client.validate_symbol('BTCUSDT')
        assert result is True
        mock_client.get_symbol_ticker.assert_called_once_with(symbol='BTCUSDT')

    @patch('src.loaders.binance_client.Client')
    def test_validate_symbol_failure(self, mock_client_class):
        """Test failed symbol validation."""
        mock_client = Mock()
        mock_client.get_symbol_ticker.side_effect = Exception("Symbol not found")
        mock_client_class.return_value = mock_client
        
        client = BinanceDataClient()
        client.client = mock_client
        
        result = client.validate_symbol('INVALID')
        assert result is False

    def test_convert_kline_to_datapoint(self):
        """Test conversion of Binance kline to HistoricalDataPoint."""
        # Sample Binance kline data
        kline = [
            1640995200000,      # Open time (2022-01-01 00:00:00)
            "47000.00",         # Open
            "48000.00",         # High
            "46500.00",         # Low
            "47500.00",         # Close
            "100.50",           # Volume
            1640998799999,      # Close time
            "4750000.00",       # Quote asset volume
            1000,               # Number of trades
            "50.25",            # Taker buy base asset volume
            "2375000.00",       # Taker buy quote asset volume
            "0"                 # Ignore
        ]
        
        datapoint = self.client._convert_kline_to_datapoint("BTCUSDT", kline)
        
        assert datapoint.symbol == "BTCUSDT"
        assert datapoint.timestamp == datetime(2022, 1, 1, 0, 0, 0)
        assert datapoint.open_price == Decimal("47000.00")
        assert datapoint.high_price == Decimal("48000.00")
        assert datapoint.low_price == Decimal("46500.00")
        assert datapoint.close_price == Decimal("47500.00")
        assert datapoint.volume == Decimal("100.50")
        assert datapoint.quote_volume == Decimal("4750000.00")
        assert datapoint.trade_count == 1000

    @pytest.mark.asyncio
    async def test_fetch_historical_klines_invalid_timeframe(self):
        """Test fetching klines with invalid timeframe."""
        with pytest.raises(ValueError, match="Unsupported timeframe"):
            await self.client.fetch_historical_klines(
                symbol="BTCUSDT",
                timeframe="invalid",
                start_date=self.start_date,
                end_date=self.end_date
            )

    @pytest.mark.asyncio
    @patch('src.loaders.binance_client.BinanceDataClient._fetch_klines_batch')
    async def test_fetch_historical_klines_success(self, mock_fetch_batch):
        """Test successful fetching of historical klines."""
        # Mock kline data
        mock_klines = [[
            1640995200000, "47000.00", "48000.00", "46500.00", "47500.00",
            "100.50", 1640998799999, "4750000.00", 1000, "50.25", "2375000.00", "0"
        ]]
        
        mock_fetch_batch.return_value = mock_klines
        
        result = await self.client.fetch_historical_klines(
            symbol="BTCUSDT",
            timeframe="1h",
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        assert len(result) == 1
        assert isinstance(result[0], HistoricalDataPoint)
        assert result[0].symbol == "BTCUSDT"

    @pytest.mark.asyncio
    @patch('src.loaders.binance_client.BinanceDataClient._fetch_klines_batch')
    async def test_fetch_historical_klines_empty_response(self, mock_fetch_batch):
        """Test fetching klines with empty response."""
        mock_fetch_batch.return_value = []
        
        result = await self.client.fetch_historical_klines(
            symbol="BTCUSDT",
            timeframe="1h",
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        assert len(result) == 0


class TestHistoricalDataLoaderBinance:
    """Test cases for HistoricalDataLoader with Binance integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = DataSourceConfig(
            source_type="api",
            api_endpoint="https://api.binance.com",
            symbols=["BTCUSDT"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
            timeframe="1h"
        )
        self.loader = HistoricalDataLoader(self.config)

    def test_config_validation_binance_no_symbols(self):
        """Test configuration validation fails when no symbols provided for Binance."""
        with pytest.raises(ValueError, match="symbols must be specified for Binance API data source"):
            DataSourceConfig(
                source_type="api",
                api_endpoint="https://api.binance.com",
                symbols=[],
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2),
                timeframe="1h"
            )

    def test_config_validation_binance_invalid_timeframe(self):
        """Test configuration validation fails with invalid Binance timeframe."""
        with pytest.raises(ValueError, match="timeframe.*not supported by Binance"):
            DataSourceConfig(
                source_type="api",
                api_endpoint="https://api.binance.com",
                symbols=["BTCUSDT"],
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2),
                timeframe="7d"  # Invalid timeframe
            )

    def test_config_validation_api_no_endpoint(self):
        """Test configuration validation fails when no API endpoint provided."""
        with pytest.raises(ValueError, match="api_endpoint is required when source_type is"):
            DataSourceConfig(
                source_type="api",
                symbols=["BTCUSDT"],
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 2),
                timeframe="1h"
            )

    @pytest.mark.asyncio
    async def test_load_from_api_unsupported_endpoint(self):
        """Test loading from unsupported API endpoint."""
        config = DataSourceConfig(
            source_type="api",
            api_endpoint="https://api.unsupported.com",
            symbols=["BTCUSDT"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
            timeframe="1h"
        )
        loader = HistoricalDataLoader(config)
        
        with pytest.raises(NotImplementedError, match="API endpoint not supported"):
            await loader._load_from_api()

    @pytest.mark.asyncio
    async def test_load_from_api_no_endpoint(self):
        """Test loading from API without endpoint."""
        config = DataSourceConfig(
            source_type="csv",  # Different source type to bypass validation
            symbols=["BTCUSDT"],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
            timeframe="1h"
        )
        config.source_type = "api"  # Change after creation
        loader = HistoricalDataLoader(config)
        
        with pytest.raises(ValueError, match="api_endpoint required for API data source"):
            await loader._load_from_api()

    @pytest.mark.asyncio
    @patch('src.loaders.data_loader.BinanceDataClient')
    async def test_load_from_binance_success(self, mock_binance_client_class):
        """Test successful loading from Binance API."""
        # Mock BinanceDataClient
        mock_client = Mock()
        mock_client.validate_symbol.return_value = True
        mock_client.fetch_historical_klines = AsyncMock(return_value=[
            HistoricalDataPoint(
                symbol="BTCUSDT",
                timestamp=datetime(2024, 1, 1, 12, 0, 0),
                open_price=Decimal("47000"),
                high_price=Decimal("48000"),
                low_price=Decimal("46500"),
                close_price=Decimal("47500"),
                volume=Decimal("100.5"),
                quote_volume=Decimal("4750000"),
                trade_count=1000
            )
        ])
        mock_binance_client_class.return_value = mock_client
        
        result = await self.loader._load_from_binance()
        
        assert len(result) == 1
        assert result[0].symbol == "BTCUSDT"
        mock_client.validate_symbol.assert_called_once_with("BTCUSDT")
        mock_client.fetch_historical_klines.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.loaders.data_loader.BinanceDataClient')
    async def test_load_from_binance_invalid_symbol(self, mock_binance_client_class):
        """Test loading from Binance with invalid symbol."""
        # Mock BinanceDataClient
        mock_client = Mock()
        mock_client.validate_symbol.return_value = False
        mock_binance_client_class.return_value = mock_client
        
        result = await self.loader._load_from_binance()
        
        assert len(result) == 0  # No data loaded for invalid symbol
        mock_client.validate_symbol.assert_called_once_with("BTCUSDT")

    @pytest.mark.asyncio
    async def test_load_from_binance_no_symbols(self):
        """Test loading from Binance without symbols."""
        config = DataSourceConfig(
            source_type="csv",  # Bypass validation
            api_endpoint="https://api.binance.com",
            symbols=[],
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
            timeframe="1h"
        )
        loader = HistoricalDataLoader(config)
        
        with pytest.raises(ValueError, match="symbols must be specified for Binance API data source"):
            await loader._load_from_binance()