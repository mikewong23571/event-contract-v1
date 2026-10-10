#!/usr/bin/env python3
"""
快速开始 - 币安分钟级K线数据获取

最简单的调用方式示例
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# 导入核心组件
from src.loaders.binance_data_downloader import BinanceDataDownloader
from src.loaders.binance_client import BinanceDataClient


# ============================================================================
# 方式1: 仅下载历史数据（离线使用）
# ============================================================================

def download_historical_data():
    """
    方式1: 下载历史数据到本地
    适用场景: 回测、离线分析
    """
    print("方式1: 下载历史数据")
    
    # 初始化下载器
    downloader = BinanceDataDownloader(data_dir=Path("./data"))
    
    # 下载单日数据
    symbol = "BTCUSDT"
    date = datetime(2024, 1, 1)
    
    async def download():
        await downloader.download_daily_data(symbol, date, "1m")
        print(f"✓ 下载完成: {symbol} {date.date()}")
    
    asyncio.run(download())


# ============================================================================
# 方式2: 实时获取最新数据（在线API）
# ============================================================================

async def get_realtime_data():
    """
    方式2: 获取实时/最新数据
    适用场景: 实时交易、最新价格监控
    """
    print("\n方式2: 获取实时数据")
    
    # 初始化客户端（纯API模式）
    client = BinanceDataClient()
    
    symbol = "BTCUSDT"
    
    # 获取最近100条1分钟K线
    data = await client.fetch_historical_klines(
        symbol=symbol,
        interval="1m",
        limit=100
    )
    
    print(f"✓ 获取到 {len(data)} 条最新数据")
    if data:
        latest = data[-1]
        print(f"  最新价格: {latest.close}")
        print(f"  时间: {latest.timestamp}")


# ============================================================================
# 方式3: 混合模式（推荐）
# ============================================================================

async def hybrid_data_access():
    """
    方式3: 混合模式 - 离线数据 + API补充
    适用场景: 大部分应用场景的最佳选择
    """
    print("\n方式3: 混合模式（推荐）")
    
    # 初始化客户端（混合模式）
    client = BinanceDataClient(
        data_dir=Path("./data"),
        offline_first=True  # 优先使用离线数据
    )
    
    symbol = "BTCUSDT"
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)  # 最近24小时
    
    # 自动使用离线数据 + API补充缺失部分
    data = await client.fetch_historical_data_hybrid(
        symbol=symbol,
        interval="1m",
        start_time=start_time,
        end_time=end_time
    )
    
    print(f"✓ 获取到 {len(data)} 条数据（离线+在线混合）")
    if data:
        print(f"  时间范围: {data[0].timestamp} 到 {data[-1].timestamp}")
        print(f"  最新价格: {data[-1].close}")


# ============================================================================
# 方式4: 批量下载多个交易对
# ============================================================================

async def batch_download():
    """
    方式4: 批量下载多个交易对的数据
    适用场景: 多币种策略、市场分析
    """
    print("\n方式4: 批量下载")
    
    downloader = BinanceDataDownloader(data_dir=Path("./data"))
    
    symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 3)
    
    for symbol in symbols:
        try:
            await downloader.download_range(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval="1m"
            )
            print(f"✓ {symbol} 下载完成")
        except Exception as e:
            print(f"✗ {symbol} 下载失败: {e}")


# ============================================================================
# 方式5: 简单的数据加载
# ============================================================================

def load_local_data():
    """
    方式5: 加载本地已下载的数据
    适用场景: 离线分析、回测
    """
    print("\n方式5: 加载本地数据")
    
    downloader = BinanceDataDownloader(data_dir=Path("./data"))
    
    # 查找本地CSV文件
    data_dir = Path("./data")
    csv_files = list(data_dir.glob("**/BTCUSDT-1m-*.csv"))
    
    if csv_files:
        # 加载第一个找到的文件
        df = downloader.load_csv_data(csv_files[0])
        print(f"✓ 加载了 {len(df)} 条记录")
        print(f"  文件: {csv_files[0].name}")
        print(f"  价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
    else:
        print("✗ 未找到本地数据文件")
        print("  提示: 先运行方式1下载数据")


# ============================================================================
# 主函数 - 选择运行方式
# ============================================================================

async def main():
    """
    主函数 - 演示不同的调用方式
    """
    print("=== 币安分钟级K线数据 - 快速调用示例 ===")
    print("\n选择运行方式:")
    print("1. 下载历史数据")
    print("2. 获取实时数据")
    print("3. 混合模式（推荐）")
    print("4. 批量下载")
    print("5. 加载本地数据")
    print("0. 运行所有示例")
    
    try:
        choice = input("\n请输入选择 (0-5): ").strip()
        
        if choice == "1":
            download_historical_data()
        elif choice == "2":
            await get_realtime_data()
        elif choice == "3":
            await hybrid_data_access()
        elif choice == "4":
            await batch_download()
        elif choice == "5":
            load_local_data()
        elif choice == "0":
            # 运行所有示例
            download_historical_data()
            await get_realtime_data()
            await hybrid_data_access()
            await batch_download()
            load_local_data()
        else:
            print("无效选择")
            return
    
    except KeyboardInterrupt:
        print("\n用户取消操作")
    except Exception as e:
        print(f"\n运行出错: {e}")
    
    print("\n=== 完成 ===")


if __name__ == "__main__":
    # 如果直接运行此文件，显示交互式菜单
    asyncio.run(main())


# ============================================================================
# 常用代码片段
# ============================================================================

"""
# 代码片段1: 最简单的数据获取
from src.loaders.binance_client import BinanceDataClient
import asyncio

async def simple_get_data():
    client = BinanceDataClient()
    data = await client.fetch_historical_klines("BTCUSDT", "1m", limit=100)
    return data

data = asyncio.run(simple_get_data())
print(f"获取到 {len(data)} 条数据")


# 代码片段2: 下载并加载数据
from src.loaders.binance_data_downloader import BinanceDataDownloader
from datetime import datetime
from pathlib import Path

downloader = BinanceDataDownloader(Path("./data"))

# 下载
async def download():
    await downloader.download_daily_data("BTCUSDT", datetime(2024, 1, 1), "1m")

asyncio.run(download())

# 加载
csv_file = Path("./data/spot/daily/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01-01.csv")
if csv_file.exists():
    df = downloader.load_csv_data(csv_file)
    print(f"加载了 {len(df)} 条记录")


# 代码片段3: 混合模式获取最近数据
from src.loaders.binance_client import BinanceDataClient
from datetime import datetime, timedelta
from pathlib import Path

client = BinanceDataClient(data_dir=Path("./data"), offline_first=True)

async def get_recent_data():
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=6)  # 最近6小时
    
    data = await client.fetch_historical_data_hybrid(
        "BTCUSDT", "1m", start_time, end_time
    )
    return data

data = asyncio.run(get_recent_data())
print(f"获取到 {len(data)} 条最近数据")
"""