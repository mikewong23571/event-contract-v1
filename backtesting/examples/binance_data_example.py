"""Example usage of Binance data loading for backtesting.

This example demonstrates how to use the backtesting engine with Binance API
to fetch historical market data for strategy testing.
"""

import asyncio
from datetime import datetime, timedelta
from src.loaders.data_loader import DataSourceConfig, HistoricalDataLoader
from src.loaders.binance_client import BinanceDataClient


async def example_basic_binance_data_loading():
    """Basic example of loading data from Binance API."""
    print("=== Basic Binance Data Loading Example ===")
    
    # Configure data source for Binance API
    config = DataSourceConfig(
        source_type="api",
        api_endpoint="https://api.binance.com",
        symbols=["BTCUSDT", "ETHUSDT"],
        start_date=datetime.now() - timedelta(days=7),  # Last 7 days
        end_date=datetime.now(),
        timeframe="1h"  # 1-hour candles
    )
    
    # Create data loader
    loader = HistoricalDataLoader(config)
    
    try:
        # Load historical data
        print("Loading data from Binance...")
        result = await loader.load_data()
        
        print(f"Loaded {result.total_records} data points")
        print(f"Symbols: {result.symbols}")
        print(f"Date range: {result.date_range['start']} to {result.date_range['end']}")
        print(f"Data quality score: {result.data_quality_score:.2f}")
        print(f"Load duration: {result.load_duration_seconds:.2f} seconds")
        
        if result.missing_periods:
            print(f"Missing periods detected: {len(result.missing_periods)}")
            for period in result.missing_periods[:3]:  # Show first 3
                print(f"  - {period['symbol']}: {period['start']} to {period['end']}")
        
        # Get data for specific symbol
        btc_data = await loader.get_data_for_symbol("BTCUSDT")
        print(f"\nBTC data points: {len(btc_data)}")
        if btc_data:
            latest = btc_data[-1]
            print(f"Latest BTC price: {latest.close_price} USDT at {latest.timestamp}")
            
    except Exception as e:
        print(f"Error loading data: {e}")


async def example_binance_client_direct():
    """Example of using BinanceDataClient directly."""
    print("\n=== Direct Binance Client Example ===")
    
    # Create Binance client (no API key needed for public data)
    client = BinanceDataClient()
    
    try:
        # Get available symbols
        print("Getting available symbols...")
        symbols = await client.get_available_symbols()
        print(f"Total available symbols: {len(symbols)}")
        print(f"First 10 symbols: {symbols[:10]}")
        
        # Validate specific symbols
        test_symbols = ["BTCUSDT", "ETHUSDT", "INVALID_SYMBOL"]
        for symbol in test_symbols:
            is_valid = client.validate_symbol(symbol)
            print(f"Symbol {symbol}: {'Valid' if is_valid else 'Invalid'}")
        
        # Get supported timeframes
        timeframes = client.get_supported_timeframes()
        print(f"\nSupported timeframes: {timeframes}")
        
        # Fetch historical data for a specific symbol
        print("\nFetching BTC historical data...")
        btc_data = await client.fetch_historical_klines(
            symbol="BTCUSDT",
            timeframe="1d",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        print(f"Fetched {len(btc_data)} daily candles for BTCUSDT")
        if btc_data:
            print(f"Price range: {min(d.low_price for d in btc_data)} - {max(d.high_price for d in btc_data)} USDT")
            
    except Exception as e:
        print(f"Error with Binance client: {e}")


async def example_data_streaming():
    """Example of streaming historical data."""
    print("\n=== Data Streaming Example ===")
    
    config = DataSourceConfig(
        source_type="api",
        api_endpoint="https://api.binance.com",
        symbols=["BTCUSDT"],
        start_date=datetime.now() - timedelta(days=2),
        end_date=datetime.now() - timedelta(days=1),
        timeframe="1h"
    )
    
    loader = HistoricalDataLoader(config)
    
    try:
        # Load data first
        await loader.load_data()
        
        # Stream data for backtesting simulation
        print("Streaming BTC data (first 10 points):")
        count = 0
        async for data_point in loader.get_data_stream("BTCUSDT"):
            print(f"  {data_point.timestamp}: O={data_point.open_price} H={data_point.high_price} L={data_point.low_price} C={data_point.close_price} V={data_point.volume}")
            count += 1
            if count >= 10:  # Limit output for example
                break
                
    except Exception as e:
        print(f"Error streaming data: {e}")


async def example_with_api_credentials():
    """Example using API credentials (optional for public data)."""
    print("\n=== API Credentials Example ===")
    
    # Note: API credentials are optional for historical data
    # They may be required for higher rate limits or private data
    api_key = "your_binance_api_key"  # Replace with actual key
    api_secret = "your_binance_api_secret"  # Replace with actual secret
    
    config = DataSourceConfig(
        source_type="api",
        api_endpoint="https://api.binance.com",
        api_key=api_key,
        api_secret=api_secret,
        symbols=["BTCUSDT"],
        start_date=datetime.now() - timedelta(days=1),
        end_date=datetime.now(),
        timeframe="15m"
    )
    
    print("Configuration with API credentials created.")
    print("Note: Replace api_key and api_secret with actual values to use.")
    
    # Uncomment below to actually load data with credentials
    # loader = HistoricalDataLoader(config)
    # result = await loader.load_data()
    # print(f"Loaded {result.total_records} data points with API credentials")


async def example_error_handling():
    """Example of error handling and validation."""
    print("\n=== Error Handling Example ===")
    
    # Test invalid timeframe
    try:
        config = DataSourceConfig(
            source_type="api",
            api_endpoint="https://api.binance.com",
            symbols=["BTCUSDT"],
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            timeframe="7d"  # Invalid timeframe for Binance
        )
    except ValueError as e:
        print(f"Validation error (expected): {e}")
    
    # Test missing symbols
    try:
        config = DataSourceConfig(
            source_type="api",
            api_endpoint="https://api.binance.com",
            symbols=[],  # Empty symbols list
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            timeframe="1h"
        )
    except ValueError as e:
        print(f"Validation error (expected): {e}")
    
    # Test invalid date range
    try:
        config = DataSourceConfig(
            source_type="api",
            api_endpoint="https://api.binance.com",
            symbols=["BTCUSDT"],
            start_date=datetime.now(),
            end_date=datetime.now() - timedelta(days=1),  # End before start
            timeframe="1h"
        )
    except ValueError as e:
        print(f"Validation error (expected): {e}")


async def main():
    """Run all examples."""
    print("Binance Data Loading Examples")
    print("=" * 50)
    
    await example_basic_binance_data_loading()
    await example_binance_client_direct()
    await example_data_streaming()
    await example_with_api_credentials()
    await example_error_handling()
    
    print("\n=== Examples Complete ===")
    print("\nNext steps:")
    print("1. Install dependencies: uv sync")
    print("2. Set up Binance API credentials (optional)")
    print("3. Run backtesting with: uv run -m src.cli.backtest_cli")
    print("4. Check the tests: uv run pytest tests/unit/test_binance_client.py")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())