"""Complete workflow example for Binance minute-level K-line data management.

This example demonstrates the complete process of:
1. Downloading historical data from Binance Data Vision
2. Managing data with automatic gap detection and filling
3. Validating data integrity and quality
4. Using hybrid approach (offline + API) for data retrieval
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our data management components
from backtesting.src.loaders.binance_data_downloader import BinanceDataDownloader, DownloadConfig
from backtesting.src.loaders.binance_client import BinanceDataClient
from backtesting.src.loaders.data_manager import DataManager
from backtesting.src.loaders.data_validator import DataValidator


async def main():
    """Main workflow demonstration."""
    
    # Configuration
    DATA_DIR = "./data/binance"
    SYMBOLS = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
    TIMEFRAME = "1m"  # 1-minute K-lines
    START_DATE = datetime(2024, 1, 1)
    END_DATE = datetime(2024, 1, 7)  # One week of data
    
    # Optional: Add your Binance API credentials for real-time data
    API_KEY = None  # "your_api_key_here"
    API_SECRET = None  # "your_api_secret_here"
    
    logger.info("=== Binance Minute-Level K-Line Data Workflow ===")
    logger.info(f"Symbols: {SYMBOLS}")
    logger.info(f"Timeframe: {TIMEFRAME}")
    logger.info(f"Date Range: {START_DATE} to {END_DATE}")
    logger.info(f"Data Directory: {DATA_DIR}")
    
    # Step 1: Initialize components
    logger.info("\n--- Step 1: Initializing Components ---")
    
    # Data downloader for bulk historical data
    download_config = DownloadConfig(
        data_dir=DATA_DIR,
        interval=TIMEFRAME,
        data_type="klines",
        market_type="spot"
    )
    downloader = BinanceDataDownloader(download_config)
    
    # Data client with hybrid capabilities
    client = BinanceDataClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        data_dir=DATA_DIR,
        prefer_offline=True
    )
    
    # Data manager for automatic gap handling
    data_manager = DataManager(
        data_dir=DATA_DIR,
        api_key=API_KEY,
        api_secret=API_SECRET
    )
    
    # Data validator for quality checks
    validator = DataValidator(data_dir=DATA_DIR)
    
    logger.info("✓ All components initialized")
    
    # Step 2: Download historical data
    logger.info("\n--- Step 2: Downloading Historical Data ---")
    
    try:
        # Download data for all symbols
        start_str = START_DATE.strftime('%Y-%m-%d')
        end_str = END_DATE.strftime('%Y-%m-%d')
        
        download_results = downloader.download_multiple_symbols(
            symbols=SYMBOLS,
            start_date=start_str,
            end_date=end_str
        )
        
        for symbol, files in download_results.items():
            logger.info(f"✓ Downloaded {len(files)} files for {symbol}")
            
    except Exception as e:
        logger.error(f"Error downloading data: {e}")
        logger.info("Continuing with existing data...")
    
    # Step 3: Validate data integrity
    logger.info("\n--- Step 3: Validating Data Integrity ---")
    
    validation_report = validator.generate_validation_report(
        symbols=SYMBOLS,
        timeframes=[TIMEFRAME],
        start_date=START_DATE,
        end_date=END_DATE
    )
    
    logger.info(f"Validation Summary:")
    logger.info(f"  - Files checked: {validation_report['summary']['total_files_checked']}")
    logger.info(f"  - Valid files: {validation_report['summary']['valid_files']}")
    logger.info(f"  - Invalid files: {validation_report['summary']['invalid_files']}")
    logger.info(f"  - Total errors: {validation_report['summary']['total_errors']}")
    logger.info(f"  - Total warnings: {validation_report['summary']['total_warnings']}")
    
    if validation_report['recommendations']:
        logger.info("Recommendations:")
        for rec in validation_report['recommendations']:
            logger.info(f"  - {rec}")
    
    # Step 4: Check and ensure data availability
    logger.info("\n--- Step 4: Ensuring Data Availability ---")
    
    availability_results = await data_manager.ensure_data_availability(
        symbols=SYMBOLS,
        timeframe=TIMEFRAME,
        start_date=START_DATE,
        end_date=END_DATE,
        auto_download=True
    )
    
    for symbol, is_available in availability_results.items():
        status = "✓ Available" if is_available else "✗ Missing"
        logger.info(f"  {symbol}: {status}")
    
    # Step 5: Detect and fill data gaps
    logger.info("\n--- Step 5: Gap Detection and Filling ---")
    
    for symbol in SYMBOLS:
        logger.info(f"\nProcessing {symbol}:")
        
        # Detect gaps
        gaps = await data_manager.get_data_gaps(
            symbol=symbol,
            timeframe=TIMEFRAME,
            start_date=START_DATE,
            end_date=END_DATE
        )
        
        if gaps:
            logger.info(f"  Found {len(gaps)} gaps")
            for i, (gap_start, gap_end) in enumerate(gaps, 1):
                logger.info(f"    Gap {i}: {gap_start} to {gap_end}")
            
            # Fill gaps using API (if credentials provided)
            if API_KEY and API_SECRET:
                logger.info(f"  Filling gaps using API...")
                success = await data_manager.fill_data_gaps(
                    symbol=symbol,
                    timeframe=TIMEFRAME,
                    gaps=gaps
                )
                if success:
                    logger.info(f"  ✓ All gaps filled successfully")
                else:
                    logger.warning(f"  ⚠ Some gaps could not be filled")
            else:
                logger.info(f"  ⚠ API credentials not provided - gaps not filled")
        else:
            logger.info(f"  ✓ No gaps found")
    
    # Step 6: Get data summary
    logger.info("\n--- Step 6: Data Summary ---")
    
    for symbol in SYMBOLS:
        summary = validator.get_data_summary(symbol, TIMEFRAME)
        logger.info(f"\n{symbol} Summary:")
        logger.info(f"  - Files: {summary['files_count']}")
        logger.info(f"  - Records: {summary['total_records']}")
        if summary['date_range']:
            start, end = summary['date_range']
            logger.info(f"  - Date range: {start} to {end}")
    
    # Step 7: Demonstrate hybrid data retrieval
    logger.info("\n--- Step 7: Hybrid Data Retrieval Demo ---")
    
    # Example: Get data for a specific period
    demo_start = START_DATE
    demo_end = START_DATE + timedelta(hours=2)  # 2 hours of minute data
    
    for symbol in SYMBOLS[:1]:  # Demo with first symbol only
        logger.info(f"\nRetrieving {symbol} data from {demo_start} to {demo_end}")
        
        try:
            # Use hybrid approach (offline + API)
            data_points = await client.fetch_historical_data_hybrid(
                symbol=symbol,
                timeframe=TIMEFRAME,
                start_date=demo_start,
                end_date=demo_end
            )
            
            logger.info(f"✓ Retrieved {len(data_points)} data points")
            
            if data_points:
                # Show first and last few data points
                logger.info("First 3 data points:")
                for i, point in enumerate(data_points[:3]):
                    logger.info(f"  {i+1}. {point.timestamp}: O={point.open_price} H={point.high_price} L={point.low_price} C={point.close_price} V={point.volume}")
                
                if len(data_points) > 3:
                    logger.info("...")
                    logger.info("Last 3 data points:")
                    for i, point in enumerate(data_points[-3:], len(data_points)-2):
                        logger.info(f"  {i}. {point.timestamp}: O={point.open_price} H={point.high_price} L={point.low_price} C={point.close_price} V={point.volume}")
            
        except Exception as e:
            logger.error(f"Error retrieving data: {e}")
    
    # Step 8: Update with latest data (if API credentials provided)
    if API_KEY and API_SECRET:
        logger.info("\n--- Step 8: Updating with Latest Data ---")
        
        update_results = await data_manager.update_latest_data(
            symbols=SYMBOLS,
            timeframe=TIMEFRAME,
            lookback_hours=1  # Get last hour of data
        )
        
        for symbol, count in update_results.items():
            logger.info(f"  {symbol}: Added {count} new data points")
    else:
        logger.info("\n--- Step 8: Skipped (No API credentials) ---")
        logger.info("To enable real-time updates, provide API_KEY and API_SECRET")
    
    logger.info("\n=== Workflow Complete ===")
    logger.info("\nNext steps:")
    logger.info("1. Use the data in your backtesting strategies")
    logger.info("2. Set up periodic updates using the DataManager")
    logger.info("3. Monitor data quality with the DataValidator")
    logger.info("4. Customize download periods and symbols as needed")


def demonstrate_advanced_features():
    """Demonstrate advanced features and configurations."""
    
    logger.info("\n=== Advanced Features Demo ===")
    
    # 1. Custom download configuration
    logger.info("\n1. Custom Download Configuration:")
    
    custom_config = DownloadConfig(
        data_dir="./custom_data",
        interval="5m",  # 5-minute intervals
        data_type="klines",
        market_type="spot",
        verify_checksums=True,  # Enable checksum verification
        max_concurrent_downloads=3  # Limit concurrent downloads
    )
    
    logger.info(f"   - Custom data directory: {custom_config.data_dir}")
    logger.info(f"   - Interval: {custom_config.interval}")
    logger.info(f"   - Checksum verification: {custom_config.verify_checksums}")
    logger.info(f"   - Max concurrent downloads: {custom_config.max_concurrent_downloads}")
    
    # 2. Data client configurations
    logger.info("\n2. Data Client Configurations:")
    
    # Prefer API over offline data
    api_first_client = BinanceDataClient(
        data_dir="./data/binance",
        prefer_offline=False  # Prefer API calls
    )
    
    # Offline-only client
    offline_only_client = BinanceDataClient(
        data_dir="./data/binance",
        prefer_offline=True
    )
    
    logger.info("   - API-first client: Prefers fresh API data")
    logger.info("   - Offline-only client: Uses cached data when available")
    
    # 3. Validation configurations
    logger.info("\n3. Data Validation Options:")
    
    validator = DataValidator(data_dir="./data/binance")
    
    # Example validation scenarios
    validation_scenarios = [
        "File structure validation",
        "Data quality checks (nulls, duplicates)",
        "Time series continuity validation",
        "OHLC price relationship validation",
        "Volume and trade count validation",
        "File integrity and checksum validation"
    ]
    
    for scenario in validation_scenarios:
        logger.info(f"   - {scenario}")
    
    logger.info("\n=== Advanced Features Demo Complete ===")


if __name__ == "__main__":
    # Run the main workflow
    asyncio.run(main())
    
    # Demonstrate advanced features
    demonstrate_advanced_features()
    
    print("\n" + "="*60)
    print("WORKFLOW COMPLETE")
    print("="*60)
    print("\nYour Binance minute-level K-line data management system is ready!")
    print("\nKey files created:")
    print("- BinanceDataDownloader: Bulk historical data download")
    print("- BinanceDataClient: Hybrid offline/API data access")
    print("- DataManager: Automatic gap detection and filling")
    print("- DataValidator: Data quality and integrity checks")
    print("\nFor production use:")
    print("1. Add your Binance API credentials for real-time updates")
    print("2. Set up automated data validation schedules")
    print("3. Configure appropriate data retention policies")
    print("4. Monitor disk space usage for large datasets")