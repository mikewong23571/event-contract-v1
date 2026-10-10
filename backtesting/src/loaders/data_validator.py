"""Data validation and integrity checking for Binance historical data."""

import hashlib
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import pandas as pd

from .data_loader import HistoricalDataPoint
from .binance_data_downloader import BinanceDataDownloader, DownloadConfig


class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


class DataValidator:
    """Validates historical data integrity and quality."""
    
    def __init__(self, data_dir: str = "./data/binance"):
        """
        Initialize data validator.
        
        Args:
            data_dir: Directory containing data files
        """
        self.data_dir = Path(data_dir)
        self.logger = logging.getLogger(__name__)
        
        # Initialize downloader for CSV loading
        download_config = DownloadConfig(data_dir=str(self.data_dir))
        self.downloader = BinanceDataDownloader(download_config)
    
    def validate_csv_file(self, csv_path: Path) -> Dict[str, Any]:
        """
        Validate a single CSV file.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'file_path': str(csv_path),
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        try:
            # Check if file exists
            if not csv_path.exists():
                validation_result['is_valid'] = False
                validation_result['errors'].append("File does not exist")
                return validation_result
            
            # Load CSV data
            df = self.downloader.load_csv_data(csv_path)
            
            if df.empty:
                validation_result['is_valid'] = False
                validation_result['errors'].append("CSV file is empty")
                return validation_result
            
            # Basic structure validation
            self._validate_csv_structure(df, validation_result)
            
            # Data quality validation
            self._validate_data_quality(df, validation_result)
            
            # Time series validation
            self._validate_time_series(df, validation_result)
            
            # Price validation
            self._validate_prices(df, validation_result)
            
            # Volume validation
            self._validate_volumes(df, validation_result)
            
            # Calculate statistics
            validation_result['stats'] = self._calculate_stats(df)
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
            self.logger.error(f"Error validating {csv_path}: {e}")
        
        return validation_result
    
    def validate_data_continuity(self,
                               symbol: str,
                               timeframe: str,
                               start_date: datetime,
                               end_date: datetime) -> Dict[str, Any]:
        """
        Validate data continuity across multiple files.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Data timeframe
            start_date: Expected start date
            end_date: Expected end date
            
        Returns:
            Dictionary with continuity validation results
        """
        validation_result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'expected_range': (start_date, end_date),
            'is_continuous': True,
            'gaps': [],
            'overlaps': [],
            'missing_periods': [],
            'total_records': 0
        }
        
        try:
            # Find all relevant CSV files
            pattern = f"{symbol}-{timeframe}-*.csv"
            csv_files = sorted(list(self.data_dir.glob(f"**/{pattern}")))
            
            if not csv_files:
                validation_result['is_continuous'] = False
                validation_result['missing_periods'].append((start_date, end_date))
                return validation_result
            
            # Load and combine all data
            all_data = []
            for csv_file in csv_files:
                try:
                    df = self.downloader.load_csv_data(csv_file)
                    if not df.empty:
                        all_data.append(df)
                except Exception as e:
                    self.logger.warning(f"Error loading {csv_file}: {e}")
                    continue
            
            if not all_data:
                validation_result['is_continuous'] = False
                validation_result['missing_periods'].append((start_date, end_date))
                return validation_result
            
            # Combine and sort data
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df = combined_df.sort_values('open_time').reset_index(drop=True)
            
            # Remove duplicates
            initial_count = len(combined_df)
            combined_df = combined_df.drop_duplicates(subset=['open_time']).reset_index(drop=True)
            final_count = len(combined_df)
            
            if initial_count > final_count:
                validation_result['overlaps'].append({
                    'duplicate_count': initial_count - final_count,
                    'message': f"Found {initial_count - final_count} duplicate records"
                })
            
            validation_result['total_records'] = final_count
            
            # Check for gaps
            gaps = self._detect_time_gaps(combined_df, timeframe)
            validation_result['gaps'] = gaps
            
            # Check coverage of expected range
            if not combined_df.empty:
                actual_start = combined_df['open_time'].min()
                actual_end = combined_df['open_time'].max()
                
                # Check if we're missing data at the beginning
                if actual_start > start_date:
                    validation_result['missing_periods'].append((start_date, actual_start))
                    validation_result['is_continuous'] = False
                
                # Check if we're missing data at the end
                if actual_end < end_date:
                    validation_result['missing_periods'].append((actual_end, end_date))
                    validation_result['is_continuous'] = False
            
            # Overall continuity assessment
            if gaps or validation_result['missing_periods']:
                validation_result['is_continuous'] = False
            
        except Exception as e:
            validation_result['is_continuous'] = False
            validation_result['error'] = str(e)
            self.logger.error(f"Error validating continuity: {e}")
        
        return validation_result
    
    def validate_data_integrity(self, csv_path: Path) -> Dict[str, Any]:
        """
        Validate data integrity using checksums and file verification.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            Dictionary with integrity validation results
        """
        integrity_result = {
            'file_path': str(csv_path),
            'file_size': 0,
            'checksum': None,
            'is_corrupted': False,
            'readable': True,
            'encoding_issues': []
        }
        
        try:
            if not csv_path.exists():
                integrity_result['readable'] = False
                return integrity_result
            
            # Get file size
            integrity_result['file_size'] = csv_path.stat().st_size
            
            # Calculate checksum
            integrity_result['checksum'] = self._calculate_file_checksum(csv_path)
            
            # Try to read the file
            try:
                df = self.downloader.load_csv_data(csv_path)
                if df.empty:
                    integrity_result['is_corrupted'] = True
            except UnicodeDecodeError as e:
                integrity_result['encoding_issues'].append(str(e))
                integrity_result['is_corrupted'] = True
            except Exception as e:
                integrity_result['is_corrupted'] = True
                integrity_result['error'] = str(e)
            
        except Exception as e:
            integrity_result['readable'] = False
            integrity_result['error'] = str(e)
            self.logger.error(f"Error checking integrity of {csv_path}: {e}")
        
        return integrity_result
    
    def generate_validation_report(self,
                                 symbols: List[str],
                                 timeframes: List[str],
                                 start_date: datetime,
                                 end_date: datetime) -> Dict[str, Any]:
        """
        Generate comprehensive validation report.
        
        Args:
            symbols: List of symbols to validate
            timeframes: List of timeframes to validate
            start_date: Start date for validation
            end_date: End date for validation
            
        Returns:
            Comprehensive validation report
        """
        report = {
            'validation_timestamp': datetime.utcnow().isoformat(),
            'parameters': {
                'symbols': symbols,
                'timeframes': timeframes,
                'date_range': (start_date.isoformat(), end_date.isoformat())
            },
            'summary': {
                'total_files_checked': 0,
                'valid_files': 0,
                'invalid_files': 0,
                'total_errors': 0,
                'total_warnings': 0
            },
            'details': {},
            'recommendations': []
        }
        
        try:
            for symbol in symbols:
                for timeframe in timeframes:
                    key = f"{symbol}_{timeframe}"
                    
                    # File validation
                    pattern = f"{symbol}-{timeframe}-*.csv"
                    csv_files = list(self.data_dir.glob(f"**/{pattern}"))
                    
                    file_validations = []
                    for csv_file in csv_files:
                        file_result = self.validate_csv_file(csv_file)
                        file_validations.append(file_result)
                        
                        report['summary']['total_files_checked'] += 1
                        if file_result['is_valid']:
                            report['summary']['valid_files'] += 1
                        else:
                            report['summary']['invalid_files'] += 1
                        
                        report['summary']['total_errors'] += len(file_result['errors'])
                        report['summary']['total_warnings'] += len(file_result['warnings'])
                    
                    # Continuity validation
                    continuity_result = self.validate_data_continuity(
                        symbol, timeframe, start_date, end_date
                    )
                    
                    report['details'][key] = {
                        'file_validations': file_validations,
                        'continuity_validation': continuity_result
                    }
            
            # Generate recommendations
            report['recommendations'] = self._generate_recommendations(report)
            
        except Exception as e:
            report['error'] = str(e)
            self.logger.error(f"Error generating validation report: {e}")
        
        return report
    
    def _validate_csv_structure(self, df: pd.DataFrame, result: Dict) -> None:
        """Validate CSV structure and required columns."""
        required_columns = [
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            result['is_valid'] = False
            result['errors'].append(f"Missing required columns: {missing_columns}")
    
    def _validate_data_quality(self, df: pd.DataFrame, result: Dict) -> None:
        """Validate data quality (nulls, duplicates, etc.)."""
        # Check for null values
        null_counts = df.isnull().sum()
        if null_counts.any():
            null_columns = null_counts[null_counts > 0].to_dict()
            result['warnings'].append(f"Null values found: {null_columns}")
        
        # Check for duplicate timestamps
        duplicate_count = df['open_time'].duplicated().sum()
        if duplicate_count > 0:
            result['warnings'].append(f"Found {duplicate_count} duplicate timestamps")
    
    def _validate_time_series(self, df: pd.DataFrame, result: Dict) -> None:
        """Validate time series properties."""
        if len(df) < 2:
            return
        
        # Check if timestamps are sorted
        if not df['open_time'].is_monotonic_increasing:
            result['errors'].append("Timestamps are not in ascending order")
            result['is_valid'] = False
        
        # Check for reasonable timestamp values
        min_time = df['open_time'].min()
        max_time = df['open_time'].max()
        
        # Timestamps should be within reasonable range (2010-2030)
        if min_time.year < 2010 or max_time.year > 2030:
            result['warnings'].append(f"Unusual timestamp range: {min_time} to {max_time}")
    
    def _validate_prices(self, df: pd.DataFrame, result: Dict) -> None:
        """Validate price data."""
        price_columns = ['open', 'high', 'low', 'close']
        
        for col in price_columns:
            if col not in df.columns:
                continue
            
            # Check for negative prices
            negative_count = (df[col] <= 0).sum()
            if negative_count > 0:
                result['errors'].append(f"Found {negative_count} non-positive {col} prices")
                result['is_valid'] = False
        
        # Check OHLC relationships
        if all(col in df.columns for col in price_columns):
            # High should be >= Open, Low, Close
            high_violations = ((df['high'] < df['open']) | 
                             (df['high'] < df['low']) | 
                             (df['high'] < df['close'])).sum()
            
            # Low should be <= Open, High, Close
            low_violations = ((df['low'] > df['open']) | 
                            (df['low'] > df['high']) | 
                            (df['low'] > df['close'])).sum()
            
            if high_violations > 0:
                result['errors'].append(f"Found {high_violations} OHLC high price violations")
                result['is_valid'] = False
            
            if low_violations > 0:
                result['errors'].append(f"Found {low_violations} OHLC low price violations")
                result['is_valid'] = False
    
    def _validate_volumes(self, df: pd.DataFrame, result: Dict) -> None:
        """Validate volume data."""
        volume_columns = ['volume', 'quote_asset_volume']
        
        for col in volume_columns:
            if col not in df.columns:
                continue
            
            # Check for negative volumes
            negative_count = (df[col] < 0).sum()
            if negative_count > 0:
                result['errors'].append(f"Found {negative_count} negative {col} values")
                result['is_valid'] = False
        
        # Check trade count
        if 'number_of_trades' in df.columns:
            negative_trades = (df['number_of_trades'] < 0).sum()
            if negative_trades > 0:
                result['errors'].append(f"Found {negative_trades} negative trade counts")
                result['is_valid'] = False
    
    def _calculate_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics for the data."""
        stats = {
            'record_count': len(df),
            'date_range': None,
            'price_stats': {},
            'volume_stats': {}
        }
        
        if not df.empty and 'open_time' in df.columns:
            stats['date_range'] = {
                'start': df['open_time'].min().isoformat(),
                'end': df['open_time'].max().isoformat()
            }
        
        # Price statistics
        price_columns = ['open', 'high', 'low', 'close']
        for col in price_columns:
            if col in df.columns:
                stats['price_stats'][col] = {
                    'min': float(df[col].min()),
                    'max': float(df[col].max()),
                    'mean': float(df[col].mean())
                }
        
        # Volume statistics
        if 'volume' in df.columns:
            stats['volume_stats'] = {
                'total_volume': float(df['volume'].sum()),
                'avg_volume': float(df['volume'].mean()),
                'max_volume': float(df['volume'].max())
            }
        
        return stats
    
    def _detect_time_gaps(self, df: pd.DataFrame, timeframe: str) -> List[Dict]:
        """Detect gaps in time series data."""
        if len(df) < 2:
            return []
        
        gaps = []
        expected_interval = self._get_interval_timedelta(timeframe)
        tolerance = timedelta(seconds=30)  # Allow 30 second tolerance
        
        for i in range(len(df) - 1):
            current_time = df.iloc[i]['open_time']
            next_time = df.iloc[i + 1]['open_time']
            expected_next = current_time + expected_interval
            
            if next_time > expected_next + tolerance:
                gaps.append({
                    'gap_start': current_time.isoformat(),
                    'gap_end': next_time.isoformat(),
                    'expected_next': expected_next.isoformat(),
                    'gap_duration': str(next_time - expected_next)
                })
        
        return gaps
    
    def _get_interval_timedelta(self, timeframe: str) -> timedelta:
        """Convert timeframe to timedelta."""
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
            '1M': timedelta(days=30)
        }
        return interval_map.get(timeframe, timedelta(minutes=1))
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _generate_recommendations(self, report: Dict) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        summary = report['summary']
        
        if summary['invalid_files'] > 0:
            recommendations.append(
                f"Fix {summary['invalid_files']} invalid files before using the data"
            )
        
        if summary['total_errors'] > 0:
            recommendations.append(
                f"Address {summary['total_errors']} data errors found during validation"
            )
        
        if summary['total_warnings'] > 0:
            recommendations.append(
                f"Review {summary['total_warnings']} warnings for potential data quality issues"
            )
        
        # Check for continuity issues
        for key, details in report['details'].items():
            continuity = details['continuity_validation']
            if not continuity['is_continuous']:
                if continuity['gaps']:
                    recommendations.append(
                        f"Fill {len(continuity['gaps'])} time gaps in {key} data"
                    )
                if continuity['missing_periods']:
                    recommendations.append(
                        f"Download missing data periods for {key}"
                    )
        
        if not recommendations:
            recommendations.append("Data validation passed - no issues found")
        
        return recommendations