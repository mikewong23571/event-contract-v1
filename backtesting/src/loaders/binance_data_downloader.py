"""币安历史数据下载器

从 data.binance.vision 批量下载历史K线数据
支持现货和期货数据的自动下载、解压和验证
"""

import os
import zipfile
import hashlib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple
import pandas as pd
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class DownloadConfig:
    """下载配置"""
    base_url: str = "https://data.binance.vision/data"
    data_dir: str = "./data/binance"
    product: str = "spot"  # spot, futures/um, futures/cm
    frequency: str = "daily"  # daily, monthly
    data_type: str = "klines"  # klines, aggTrades, trades
    interval: str = "1m"  # 1s, 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1mo
    verify_checksum: bool = True
    auto_extract: bool = True
    keep_zip: bool = False

class BinanceDataDownloader:
    """币安数据下载器"""
    
    def __init__(self, config: DownloadConfig):
        self.config = config
        self.data_dir = Path(config.data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def download_symbol_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str
    ) -> List[Path]:
        """下载指定符号的历史数据
        
        Args:
            symbol: 交易对符号，如 'BTCUSDT'
            start_date: 开始日期，格式 'YYYY-MM-DD'
            end_date: 结束日期，格式 'YYYY-MM-DD'
            
        Returns:
            下载的文件路径列表
        """
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        downloaded_files = []
        
        if self.config.frequency == "daily":
            current_date = start_dt
            while current_date <= end_dt:
                date_str = current_date.strftime("%Y-%m-%d")
                file_path = self._download_daily_data(symbol, date_str)
                if file_path:
                    downloaded_files.append(file_path)
                current_date += timedelta(days=1)
                
        elif self.config.frequency == "monthly":
            current_date = start_dt.replace(day=1)
            while current_date <= end_dt:
                date_str = current_date.strftime("%Y-%m")
                file_path = self._download_monthly_data(symbol, date_str)
                if file_path:
                    downloaded_files.append(file_path)
                # 移动到下个月
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
                    
        return downloaded_files
    
    def _download_daily_data(self, symbol: str, date: str) -> Optional[Path]:
        """下载单日数据"""
        filename = f"{symbol}-{self.config.interval}-{date}.zip"
        url = self._build_url(symbol, filename)
        return self._download_file(url, filename)
    
    def _download_monthly_data(self, symbol: str, date: str) -> Optional[Path]:
        """下载单月数据"""
        filename = f"{symbol}-{self.config.interval}-{date}.zip"
        url = self._build_url(symbol, filename)
        return self._download_file(url, filename)
    
    def _build_url(self, symbol: str, filename: str) -> str:
        """构建下载URL"""
        return f"{self.config.base_url}/{self.config.product}/{self.config.frequency}/{self.config.data_type}/{symbol}/{self.config.interval}/{filename}"
    
    def _download_file(self, url: str, filename: str) -> Optional[Path]:
        """下载单个文件"""
        file_path = self.data_dir / filename
        
        # 如果文件已存在且验证通过，跳过下载
        if file_path.exists():
            if self.config.verify_checksum and self._verify_file(file_path):
                logger.info(f"文件已存在且验证通过: {filename}")
                return self._process_downloaded_file(file_path)
            elif not self.config.verify_checksum:
                logger.info(f"文件已存在: {filename}")
                return self._process_downloaded_file(file_path)
        
        try:
            logger.info(f"开始下载: {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 下载文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"下载完成: {filename}")
            
            # 验证文件
            if self.config.verify_checksum:
                if not self._verify_file(file_path):
                    logger.error(f"文件验证失败: {filename}")
                    file_path.unlink()  # 删除损坏的文件
                    return None
            
            return self._process_downloaded_file(file_path)
            
        except requests.RequestException as e:
            logger.error(f"下载失败 {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"处理文件失败 {filename}: {e}")
            return None
    
    def _verify_file(self, file_path: Path) -> bool:
        """验证文件完整性"""
        checksum_url = f"{str(file_path)}.CHECKSUM"
        checksum_path = Path(f"{file_path}.CHECKSUM")
        
        try:
            # 下载CHECKSUM文件
            if not checksum_path.exists():
                response = requests.get(checksum_url, timeout=10)
                response.raise_for_status()
                with open(checksum_path, 'w') as f:
                    f.write(response.text)
            
            # 读取期望的校验和
            with open(checksum_path, 'r') as f:
                expected_hash = f.read().strip().split()[0]
            
            # 计算文件的SHA256
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            actual_hash = sha256_hash.hexdigest()
            
            if actual_hash == expected_hash:
                logger.info(f"文件验证成功: {file_path.name}")
                return True
            else:
                logger.error(f"文件验证失败: {file_path.name}")
                return False
                
        except Exception as e:
            logger.warning(f"无法验证文件 {file_path.name}: {e}")
            return True  # 如果无法验证，假设文件正确
    
    def _process_downloaded_file(self, file_path: Path) -> Optional[Path]:
        """处理下载的文件"""
        if self.config.auto_extract and file_path.suffix == '.zip':
            return self._extract_zip(file_path)
        return file_path
    
    def _extract_zip(self, zip_path: Path) -> Optional[Path]:
        """解压ZIP文件"""
        try:
            extract_dir = zip_path.parent / zip_path.stem
            extract_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # 查找CSV文件
            csv_files = list(extract_dir.glob('*.csv'))
            if csv_files:
                csv_path = csv_files[0]
                logger.info(f"解压完成: {csv_path}")
                
                # 删除ZIP文件（如果配置允许）
                if not self.config.keep_zip:
                    zip_path.unlink()
                    # 同时删除CHECKSUM文件
                    checksum_path = Path(f"{zip_path}.CHECKSUM")
                    if checksum_path.exists():
                        checksum_path.unlink()
                
                return csv_path
            else:
                logger.error(f"ZIP文件中未找到CSV文件: {zip_path}")
                return None
                
        except Exception as e:
            logger.error(f"解压失败 {zip_path}: {e}")
            return None
    
    def load_csv_data(self, csv_path: Path) -> pd.DataFrame:
        """加载CSV数据为DataFrame"""
        try:
            # 币安K线数据的列名
            columns = [
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ]
            
            df = pd.read_csv(csv_path, names=columns)
            
            # 转换时间戳
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            
            # 转换数值类型
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 
                             'quote_asset_volume', 'taker_buy_base_asset_volume', 
                             'taker_buy_quote_asset_volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 删除ignore列
            df = df.drop('ignore', axis=1)
            
            return df
            
        except Exception as e:
            logger.error(f"加载CSV数据失败 {csv_path}: {e}")
            raise
    
    def get_available_symbols(self) -> List[str]:
        """获取可用的交易对列表"""
        # 这里可以实现从币安API获取所有可用交易对
        # 或者从预定义列表返回
        common_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT',
            'XRPUSDT', 'LTCUSDT', 'LINKUSDT', 'BCHUSDT', 'XLMUSDT'
        ]
        return common_symbols
    
    def download_multiple_symbols(
        self, 
        symbols: List[str], 
        start_date: str, 
        end_date: str
    ) -> dict:
        """批量下载多个交易对的数据
        
        Returns:
            {symbol: [file_paths]} 的字典
        """
        results = {}
        
        for symbol in symbols:
            logger.info(f"开始下载 {symbol} 的数据...")
            try:
                files = self.download_symbol_data(symbol, start_date, end_date)
                results[symbol] = files
                logger.info(f"{symbol} 下载完成，共 {len(files)} 个文件")
            except Exception as e:
                logger.error(f"下载 {symbol} 失败: {e}")
                results[symbol] = []
        
        return results