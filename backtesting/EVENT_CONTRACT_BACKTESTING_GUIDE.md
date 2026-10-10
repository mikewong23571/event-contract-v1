# Event Contract Backtesting Engine - 专业指南

## 概述

本事件合约回测引擎是一个专为币安事件合约交易设计的高性能、专业级回测系统。该引擎针对二元结算机制进行了深度优化，内置55.6%隐含概率计算模型，支持并行处理和多时间周期分析。

## 核心特性

### 🎯 事件合约专用功能
- **二元结算机制模拟器**: 精确模拟事件合约的二元结算过程
- **55.6%隐含概率模型**: 内置盈亏平衡点计算，确保策略的数学合理性
- **固定赔率处理**: 支持80%标准赔率和自定义赔率配置
- **合约到期管理**: 自动处理合约到期和结算逻辑

### 📊 高级数据处理
- **多时间周期支持**: 1分钟到1天的全时间周期覆盖
- **智能数据缓存**: 多层缓存机制，显著提升数据加载速度
- **数据质量评估**: 自动检测数据缺失和异常值
- **币安API集成**: 直接从币安获取历史数据

### ⚡ 性能优化
- **并行计算架构**: 支持多线程和多进程并行处理
- **策略执行缓存**: 避免重复计算，提升回测效率
- **内存优化管理**: 智能内存使用，支持大规模数据处理
- **批量处理**: 高效的批量数据处理机制

### 🔍 波动率分析
- **实时波动率计算**: 多种波动率估算方法（Parkinson、Garman-Klass等）
- **趋势反转检测**: 智能识别市场反转信号
- **突破检测**: 自动识别价格突破和假突破
- **市场状态分类**: 趋势、震荡、突破等市场状态识别

### 🛠 集成接口
- **SDK接口**: 完整的Python SDK，支持程序化调用
- **命令行工具**: 功能完整的CLI，支持批量操作
- **多格式输出**: JSON、CSV、Parquet、Excel等格式支持
- **Webhook通知**: 支持回测完成后的自动通知

### 📈 监控系统
- **实时性能监控**: CPU、内存、磁盘使用率监控
- **详细日志记录**: 结构化日志，便于问题追踪
- **告警系统**: 资源使用和性能异常告警
- **指标导出**: 支持Prometheus等监控系统集成

## 快速开始

### 安装依赖

```bash
# 进入backtesting目录
cd backtesting

# 安装依赖
uv sync

# 安装开发依赖（可选）
uv sync --extra dev
```

### 基础使用示例

#### 1. 命令行快速回测

```bash
# 基础单策略回测
backtest --strategy-name "volatility_strategy" \
         --symbols "BTCUSDT" \
         --timeframes "15m" \
         --start-date "2024-01-01" \
         --end-date "2024-01-31"

# 多币种组合回测
backtest --strategy-name "portfolio_strategy" \
         --symbols "BTCUSDT,ETHUSDT,ADAUSDT" \
         --timeframes "15m,1h" \
         --mode "multi_symbol" \
         --processing-mode "PARALLEL_THREAD"

# 参数优化回测
backtest --strategy-name "optimized_strategy" \
         --symbols "BTCUSDT" \
         --timeframes "15m" \
         --mode "optimization" \
         --parameters '{"volatility_threshold": [0.02, 0.03, 0.05], "confidence_level": [0.6, 0.7, 0.8]}'
```

#### 2. SDK编程接口

```python
import asyncio
from datetime import datetime
from decimal import Decimal

from src.sdk.event_contract_sdk import (
    EventContractBacktestSDK, SDKConfig, BacktestRequest, BacktestMode
)
from src.loaders.binance_event_data_processor import TimeFrame
from src.strategies.event_contract_strategy import EventContractStrategyConfig

async def run_backtest_example():
    # 配置SDK
    sdk_config = SDKConfig(
        default_output_format="json",
        enable_detailed_logging=True
    )
    
    # 创建策略配置
    strategy_config = EventContractStrategyConfig(
        name="example_strategy",
        description="示例波动率策略",
        custom_parameters={
            "volatility_threshold": 0.03,
            "confidence_threshold": 0.7
        }
    )
    
    # 创建回测请求
    request = BacktestRequest(
        symbols=["BTCUSDT", "ETHUSDT"],
        timeframes=[TimeFrame.M15, TimeFrame.H1],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        strategy_configs=[strategy_config],
        mode=BacktestMode.MULTI_SYMBOL,
        initial_capital=Decimal('10000.0')
    )
    
    # 执行回测
    sdk = EventContractBacktestSDK(sdk_config)
    response = await sdk.run_backtest(request)
    
    # 处理结果
    if response.success:
        print(f"回测完成，总收益: {sum(float(r.total_profit_loss) for r in response.results):.2f}")
        print(f"平均胜率: {sum(float(r.win_rate) for r in response.results) / len(response.results):.2%}")
    else:
        print(f"回测失败: {response.error_message}")

# 运行示例
asyncio.run(run_backtest_example())
```

#### 3. 自定义策略开发

```python
from src.strategies.event_contract_strategy import (
    BaseEventContractStrategy, EventContractSignal, MarketCondition, SignalStrength
)
from src.loaders.binance_event_data_processor import ProcessedDataPoint, TimeFrame
from src.simulators.event_contract_simulator import ContractDirection

class VolatilityBreakoutStrategy(BaseEventContractStrategy):
    """基于波动率突破的事件合约策略"""
    
    async def analyze_market_conditions(self, data):
        # 分析市场状态
        latest_data = data[self.config.primary_timeframe][-1]
        
        if latest_data.volatility > Decimal('0.05'):
            return MarketCondition.VOLATILE
        elif latest_data.volatility < Decimal('0.01'):
            return MarketCondition.SIDEWAYS
        else:
            return MarketCondition.TRENDING_UP if latest_data.price_change > 0 else MarketCondition.TRENDING_DOWN
    
    async def generate_signal(self, current_data, historical_data):
        # 获取历史数据
        recent_data = self.get_historical_data(self.config.primary_timeframe, 20)
        
        if len(recent_data) < 20:
            return None
        
        # 计算波动率突破
        current_volatility = current_data.volatility
        avg_volatility = sum(d.volatility for d in recent_data[-10:]) / 10
        
        # 检查突破条件
        if current_volatility > avg_volatility * Decimal('1.5'):
            # 确定方向
            direction = ContractDirection.UP if current_data.price_change > 0 else ContractDirection.DOWN
            
            # 计算置信度
            volatility_ratio = float(current_volatility / avg_volatility)
            confidence_score = min(volatility_ratio / 2.0, 1.0)
            
            # 生成信号
            signal = EventContractSignal(
                timestamp=current_data.timestamp,
                symbol=current_data.symbol,
                direction=direction,
                strength=SignalStrength.STRONG if confidence_score > 0.8 else SignalStrength.MODERATE,
                confidence_score=Decimal(str(confidence_score)),
                predicted_probability=Decimal('0.65'),  # 基于历史回测优化
                suggested_duration_minutes=60,
                suggested_bet_amount=Decimal('100.0'),
                max_bet_amount=Decimal('500.0'),
                risk_level=self.assess_risk_level(None, MarketCondition.VOLATILE),
                market_condition=MarketCondition.VOLATILE,
                volatility_score=current_volatility,
                entry_price=current_data.close_price,
                primary_indicator="volatility_breakout",
                signal_reason=f"波动率突破: {volatility_ratio:.2f}x平均值",
                strategy_name=self.name,
                timeframe_analyzed=self.config.primary_timeframe
            )
            
            return signal
        
        return None
    
    def calculate_position_size(self, signal, available_capital, current_risk_exposure):
        # 基于Kelly准则的仓位计算
        win_prob = signal.predicted_probability
        payout_ratio = Decimal('0.8')  # 80%赔率
        
        kelly_size = self.calculate_kelly_position_size(win_prob, payout_ratio, available_capital)
        
        # 应用风险限制
        max_position = available_capital * self.config.position_sizing.max_bet_percentage
        
        return min(kelly_size, max_position, signal.max_bet_amount)
    
    def assess_risk_level(self, signal, market_condition):
        # 根据市场状态评估风险
        if market_condition == MarketCondition.VOLATILE:
            return "HIGH"
        elif market_condition == MarketCondition.SIDEWAYS:
            return "LOW"
        else:
            return "MEDIUM"
```

## 高级功能

### 并行处理配置

```python
from src.engines.parallel_backtest_engine import (
    PerformanceOptimizationConfig, ProcessingMode, CacheStrategy
)

# 高性能配置
perf_config = PerformanceOptimizationConfig(
    processing_mode=ProcessingMode.PARALLEL_PROCESS,  # 多进程处理
    max_workers=8,  # 8个工作进程
    cache_strategy=CacheStrategy.HYBRID_CACHE,  # 混合缓存
    max_memory_usage_gb=8.0,  # 最大内存使用
    enable_strategy_caching=True,  # 启用策略缓存
    parallel_strategy_execution=True  # 并行策略执行
)
```

### 数据处理优化

```python
from src.loaders.binance_event_data_processor import (
    DataProcessingConfig, BinanceEventDataProcessor
)

# 数据处理配置
data_config = DataProcessingConfig(
    cache_directory=Path("data/cache"),
    enable_caching=True,
    cache_compression=True,
    max_cache_age_hours=24,
    parallel_processing=True,
    max_workers=4,
    outlier_detection=True,
    validate_price_consistency=True
)

# 多时间周期数据加载
processor = BinanceEventDataProcessor(data_config)
multi_tf_data = await processor.get_multi_timeframe_data(
    symbol="BTCUSDT",
    timeframes=[TimeFrame.M5, TimeFrame.M15, TimeFrame.H1],
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)
```

### 性能监控

```python
from src.monitoring.performance_monitor import (
    PerformanceMonitor, MonitoringConfig
)

# 监控配置
monitoring_config = MonitoringConfig(
    enable_metrics=True,
    enable_resource_monitoring=True,
    enable_alerting=True,
    cpu_usage_threshold=80.0,
    memory_usage_threshold=85.0,
    log_level="INFO"
)

# 启动监控
monitor = PerformanceMonitor(monitoring_config)
await monitor.start_monitoring()

# 使用监控装饰器
async with monitor.time_operation("backtest_execution"):
    # 执行回测代码
    result = await run_backtest()

# 获取性能报告
performance_summary = monitor.get_performance_summary()
print(f"平均CPU使用率: {performance_summary['resource_summary']['average_cpu_percent']:.1f}%")
```

## 系统管理

### 健康检查

```bash
# 系统健康检查
backtest health

# 获取系统状态
backtest status

# 清理缓存
backtest clear-cache
```

### 日志管理

日志文件位置：`logs/backtest.log`

日志级别配置：
- `DEBUG`: 详细调试信息
- `INFO`: 一般信息（默认）
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 缓存管理

缓存目录：`data/cache/`

缓存类型：
- **数据缓存**: 历史价格数据
- **策略缓存**: 策略执行结果
- **指标缓存**: 技术指标计算结果

## 性能优化建议

### 1. 数据加载优化
- 启用数据缓存，避免重复下载
- 使用Parquet格式存储大量数据
- 合理设置批处理大小

### 2. 并行处理优化
- 根据CPU核心数设置工作进程数
- 大数据集使用多进程，小数据集使用多线程
- 启用策略执行缓存

### 3. 内存管理
- 设置合理的内存使用限制
- 定期清理过期缓存
- 使用数据分块处理大型数据集

### 4. 策略优化
- 避免在策略中进行重复计算
- 使用向量化操作处理技术指标
- 合理设置回看周期长度

## 故障排除

### 常见问题

1. **内存不足错误**
   - 减少并行工作进程数
   - 降低数据缓存大小
   - 使用数据分块处理

2. **数据加载失败**
   - 检查网络连接
   - 验证API密钥配置
   - 确认数据时间范围有效

3. **策略执行缓慢**
   - 启用并行处理
   - 优化策略算法
   - 使用策略缓存

4. **结果不一致**
   - 检查数据质量
   - 验证策略逻辑
   - 确认随机种子设置

### 调试技巧

1. **启用详细日志**
   ```bash
   backtest --verbose backtest --strategy-name "debug_strategy" ...
   ```

2. **使用性能分析**
   ```python
   # 启用性能分析
   config.enable_profiling = True
   config.profile_output_dir = Path("profiles")
   ```

3. **监控资源使用**
   ```python
   # 实时监控
   monitor = PerformanceMonitor(config)
   await monitor.start_monitoring()
   ```

## 最佳实践

### 策略开发
1. **遵循接口契约**: 继承BaseEventContractStrategy
2. **参数化设计**: 使用配置文件管理策略参数
3. **风险控制**: 实现完整的风险管理逻辑
4. **回测验证**: 多时间段验证策略稳定性

### 数据管理
1. **数据质量**: 定期检查数据完整性
2. **缓存策略**: 合理设置缓存过期时间
3. **存储优化**: 使用压缩格式存储历史数据
4. **备份机制**: 定期备份重要数据

### 性能优化
1. **资源监控**: 持续监控系统资源使用
2. **并行配置**: 根据硬件配置优化并行参数
3. **缓存利用**: 充分利用各级缓存机制
4. **代码优化**: 定期优化热点代码路径

## 技术支持

### 文档资源
- API文档：`docs/api.md`
- 架构设计：`docs/architecture.md`
- 开发指南：`docs/development.md`

### 社区支持
- GitHub Issues: 报告问题和功能请求
- 讨论区: 技术交流和经验分享
- 示例代码: `examples/` 目录

### 联系方式
- 技术支持邮箱: support@example.com
- 开发者社区: https://community.example.com
- 官方文档: https://docs.example.com

---

**注意**: 本回测引擎仅用于策略研究和历史数据分析，不构成投资建议。实际交易前请充分了解相关风险。