#!/usr/bin/env python3
"""
币安分钟级K线数据管理系统使用示例

本示例展示如何使用我们构建的数据管理系统来获取和管理币安的分钟级K线数据。
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# 导入我们的数据管理组件
from src.loaders.binance_data_downloader import BinanceDataDownloader
from src.loaders.binance_client import BinanceDataClient
from src.loaders.data_manager import DataManager
from src.loaders.data_validator import DataValidator


async def main():
    """
    主函数：演示完整的数据获取和管理流程
    """
    print("=== 币安分钟级K线数据管理系统使用示例 ===")
    
    # 1. 配置数据存储路径
    data_dir = Path("./data/binance")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. 初始化组件
    print("\n1. 初始化数据管理组件...")
    
    # 历史数据下载器
    downloader = BinanceDataDownloader(data_dir=data_dir)
    
    # 币安数据客户端（支持离线+在线混合模式）
    client = BinanceDataClient(
        data_dir=data_dir,
        offline_first=True  # 优先使用离线数据
    )
    
    # 数据管理器
    manager = DataManager(
        downloader=downloader,
        client=client,
        data_dir=data_dir
    )
    
    # 数据验证器
    validator = DataValidator()
    
    # 3. 下载历史数据示例
    print("\n2. 下载历史数据...")
    symbol = "BTCUSDT"
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 7)  # 下载一周的数据
    
    try:
        # 下载指定时间范围的1分钟K线数据
        await downloader.download_range(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval="1m"
        )
        print(f"✓ 成功下载 {symbol} 从 {start_date.date()} 到 {end_date.date()} 的数据")
    except Exception as e:
        print(f"✗ 下载失败: {e}")
    
    # 4. 数据验证示例
    print("\n3. 验证数据完整性...")
    csv_files = list(data_dir.glob(f"**/{symbol}-1m-*.csv"))
    if csv_files:
        # 验证第一个文件
        validation_result = validator.validate_csv_file(csv_files[0])
        print(f"文件验证结果: {'✓ 通过' if validation_result['is_valid'] else '✗ 失败'}")
        if validation_result['errors']:
            print(f"错误信息: {validation_result['errors']}")
    
    # 5. 混合数据获取示例
    print("\n4. 使用混合模式获取数据...")
    try:
        # 获取最近7天的数据（会自动使用离线数据+API补充）
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        data = await client.fetch_historical_data_hybrid(
            symbol=symbol,
            interval="1m",
            start_time=start_time,
            end_time=end_time
        )
        
        print(f"✓ 获取到 {len(data)} 条数据点")
        if data:
            print(f"  时间范围: {data[0].timestamp} 到 {data[-1].timestamp}")
            print(f"  最新价格: {data[-1].close}")
    
    except Exception as e:
        print(f"✗ 数据获取失败: {e}")
    
    # 6. 数据管理示例
    print("\n5. 检查和补充缺失数据...")
    try:
        # 检查数据可用性
        availability = await manager.check_data_availability(
            symbol=symbol,
            interval="1m",
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"数据可用性: {availability['coverage_percentage']:.1f}%")
        
        if availability['missing_dates']:
            print(f"缺失日期: {len(availability['missing_dates'])} 天")
            
            # 自动补充缺失数据
            filled_count = await manager.fill_data_gaps(
                symbol=symbol,
                interval="1m",
                start_date=start_date,
                end_date=end_date
            )
            print(f"✓ 补充了 {filled_count} 天的数据")
    
    except Exception as e:
        print(f"✗ 数据管理失败: {e}")
    
    # 7. 获取数据摘要
    print("\n6. 数据摘要...")
    try:
        summary = await manager.get_data_summary(symbol, "1m")
        print(f"总数据文件: {summary['total_files']}")
        print(f"数据大小: {summary['total_size_mb']:.2f} MB")
        print(f"时间范围: {summary['date_range']['start']} 到 {summary['date_range']['end']}")
        print(f"总数据点: {summary['total_records']:,}")
    except Exception as e:
        print(f"✗ 获取摘要失败: {e}")
    
    print("\n=== 示例完成 ===")


def quick_usage_example():
    """
    快速使用示例 - 同步版本
    """
    print("\n=== 快速使用示例 ===")
    
    # 简单的历史数据下载
    data_dir = Path("./data/binance")
    downloader = BinanceDataDownloader(data_dir=data_dir)
    
    # 下载单日数据
    symbol = "ETHUSDT"
    date = datetime(2024, 1, 1)
    
    try:
        # 同步下载
        asyncio.run(downloader.download_daily_data(symbol, date, "1m"))
        print(f"✓ 成功下载 {symbol} {date.date()} 的1分钟数据")
        
        # 加载数据
        csv_file = data_dir / "spot" / "daily" / "klines" / symbol / "1m" / f"{symbol}-1m-{date.strftime('%Y-%m-%d')}.csv"
        if csv_file.exists():
            df = downloader.load_csv_data(csv_file)
            print(f"✓ 加载了 {len(df)} 条记录")
            print(f"  价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
    
    except Exception as e:
        print(f"✗ 快速示例失败: {e}")


if __name__ == "__main__":
    # 运行完整示例
    asyncio.run(main())
    
    # 运行快速示例
    quick_usage_example()
    
    print("\n💡 提示:")
    print("- 首次运行需要下载数据，可能需要一些时间")
    print("- 确保网络连接正常以访问币安API")
    print("- 数据会保存在 ./data/binance 目录下")
    print("- 可以修改 symbol、日期范围等参数来测试不同场景")
    print("\n📚 更多信息请查看: docs/binance_data_management.md")