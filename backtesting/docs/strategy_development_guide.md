# 策略开发指南

本指南将详细介绍如何在币安分钟级K线数据管理系统中创建和实现自定义交易策略。

## 目录

1. [策略架构概述](#策略架构概述)
2. [基础策略接口](#基础策略接口)
3. [创建自定义策略](#创建自定义策略)
4. [技术指标计算](#技术指标计算)
5. [信号生成逻辑](#信号生成逻辑)
6. [策略配置管理](#策略配置管理)
7. [风险管理](#风险管理)
8. [策略测试](#策略测试)
9. [最佳实践](#最佳实践)
10. [常见问题](#常见问题)

## 策略架构概述

### 核心组件

我们的策略系统基于以下核心组件构建：

- **BaseStrategy**: 所有策略的抽象基类
- **StrategyConfig**: 策略配置管理
- **StrategySignal**: 交易信号数据结构
- **TechnicalIndicators**: 技术指标容器
- **HistoricalDataPoint**: 历史数据点

### 策略生命周期

```
初始化 → 数据更新 → 指标计算 → 信号生成 → 信号验证 → 输出结果
```

## 基础策略接口

### BaseStrategy 类

所有自定义策略必须继承自 `BaseStrategy` 类：

```python
from backtesting.src.strategies.base_strategy import BaseStrategy, StrategySignal, TechnicalIndicators
from backtesting.src.loaders.data_loader import HistoricalDataPoint

class MyCustomStrategy(BaseStrategy):
    def __init__(self, config: Optional[MyStrategyConfig] = None):
        super().__init__(config)
        # 初始化策略特定参数
    
    async def generate_signal(self, data_point: HistoricalDataPoint) -> Optional[StrategySignal]:
        # 实现信号生成逻辑
        pass
    
    def calculate_indicators(self, data_point: HistoricalDataPoint) -> TechnicalIndicators:
        # 实现技术指标计算
        pass
```

### 必须实现的方法

1. **`generate_signal()`**: 核心信号生成方法
2. **`calculate_indicators()`**: 技术指标计算方法

### 可选重写的方法

- **`validate_signal_conditions()`**: 自定义信号验证逻辑
- **`should_generate_signal()`**: 信号生成条件检查
- **`get_risk_parameters()`**: 风险参数获取

## 创建自定义策略

### 步骤 1: 定义策略配置

```python
from backtesting.src.strategies.base_strategy import StrategyConfig

class MyStrategyConfig(StrategyConfig):
    def __init__(self, **kwargs):
        # 设置策略特定的默认参数
        default_params = {
            "indicator_period": 14,
            "threshold_value": 0.02,
            "confirmation_periods": 2,
            # 添加更多参数...
        }
        
        # 合并用户提供的参数
        if 'parameters' in kwargs:
            default_params.update(kwargs['parameters'])
        kwargs['parameters'] = default_params
        
        # 设置策略基本信息
        kwargs.setdefault('name', 'MyCustomStrategy')
        kwargs.setdefault('description', '我的自定义交易策略')
        kwargs.setdefault('min_confidence', 'MEDIUM')
        kwargs.setdefault('min_probability', 0.60)
        
        super().__init__(**kwargs)
```

### 步骤 2: 实现策略类

```python
class MyCustomStrategy(BaseStrategy):
    def __init__(self, config: Optional[MyStrategyConfig] = None):
        if config is None:
            config = MyStrategyConfig()
        super().__init__(config)
        
        # 提取策略参数
        params = self.config.parameters
        self.indicator_period = params['indicator_period']
        self.threshold_value = params['threshold_value']
        self.confirmation_periods = params['confirmation_periods']
    
    async def generate_signal(self, data_point: HistoricalDataPoint) -> Optional[StrategySignal]:
        # 更新数据
        self.update_data(data_point)
        
        # 检查是否有足够的历史数据
        if len(self._price_history) < self.indicator_period + 5:
            return None
        
        # 计算技术指标
        indicators = self.get_indicators()
        if not indicators:
            return None
        
        # 分析市场条件
        signal_direction = self._analyze_conditions(indicators, data_point)
        if not signal_direction:
            return None
        
        # 计算信号强度
        confidence, probability = self._calculate_signal_strength(indicators, signal_direction)
        
        # 创建信号
        signal = StrategySignal(
            timestamp=data_point.timestamp,
            symbol=data_point.symbol,
            direction=signal_direction,
            confidence=confidence,
            probability=probability,
            expiry_minutes=self.config.contract_duration_minutes,
            strategy_name=self.name,
            strategy_version=self.version,
            indicators=indicators,
            entry_price=data_point.close_price,
            signal_reason=self._generate_signal_reason(indicators, signal_direction),
            conditions_met=self._get_conditions_met(indicators, signal_direction),
            risk_level=self._assess_risk_level(indicators)
        )
        
        # 验证信号
        if not self.validate_signal_conditions(signal):
            return None
        
        self._signals_generated += 1
        self._last_signal_time = data_point.timestamp
        
        return signal
    
    def calculate_indicators(self, data_point: HistoricalDataPoint) -> TechnicalIndicators:
        indicators = TechnicalIndicators()
        
        # 计算基础指标
        indicators.sma_20 = self._calculate_sma(20)
        indicators.rsi = self._calculate_rsi(self.indicator_period)
        indicators.volatility = self._calculate_volatility(20)
        
        # 计算自定义指标
        indicators.custom = {
            'my_indicator': self._calculate_my_indicator(),
            'signal_strength': self._calculate_signal_strength_indicator()
        }
        
        return indicators
```

## 技术指标计算

### 内置指标方法

BaseStrategy 提供了常用技术指标的计算方法：

```python
# 移动平均线
sma_20 = self._calculate_sma(20)
ema_12 = self._calculate_ema(12)

# 相对强弱指数
rsi = self._calculate_rsi(14)

# 波动率
volatility = self._calculate_volatility(20)

# 价格变化
price_change = self._calculate_price_change(1)  # 1期价格变化
price_change_pct = self._calculate_price_change_pct(1)  # 1期价格变化百分比
```

### 自定义指标实现

```python
def _calculate_my_indicator(self) -> Optional[float]:
    """计算自定义指标。"""
    if len(self._price_history) < self.indicator_period:
        return None
    
    # 获取最近的价格数据
    recent_prices = [float(dp.close_price) for dp in self._price_history[-self.indicator_period:]]
    
    # 实现你的指标计算逻辑
    # 例如：计算价格动量
    momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
    
    return momentum

def _calculate_bollinger_bands(self, period: int = 20, std_dev: float = 2.0) -> tuple:
    """计算布林带。"""
    if len(self._price_history) < period:
        return None, None, None
    
    prices = [float(dp.close_price) for dp in self._price_history[-period:]]
    sma = sum(prices) / len(prices)
    
    # 计算标准差
    variance = sum((price - sma) ** 2 for price in prices) / len(prices)
    std = math.sqrt(variance)
    
    upper_band = sma + (std_dev * std)
    lower_band = sma - (std_dev * std)
    
    return sma, upper_band, lower_band
```

## 信号生成逻辑

### 信号方向判断

```python
def _analyze_conditions(self, indicators: TechnicalIndicators, 
                       data_point: HistoricalDataPoint) -> Optional[str]:
    """分析市场条件，确定信号方向。"""
    current_price = float(data_point.close_price)
    
    # 定义买入条件
    buy_conditions = [
        indicators.rsi and indicators.rsi < 30,  # RSI超卖
        indicators.sma_20 and current_price > indicators.sma_20,  # 价格在均线上方
        indicators.custom.get('my_indicator', 0) > self.threshold_value,  # 自定义指标条件
        self._check_volume_confirmation(indicators)  # 成交量确认
    ]
    
    # 定义卖出条件
    sell_conditions = [
        indicators.rsi and indicators.rsi > 70,  # RSI超买
        indicators.sma_20 and current_price < indicators.sma_20,  # 价格在均线下方
        indicators.custom.get('my_indicator', 0) < -self.threshold_value,  # 自定义指标条件
        self._check_volume_confirmation(indicators)  # 成交量确认
    ]
    
    # 检查条件（需要满足大部分条件）
    if sum(buy_conditions) >= 3:
        return "UP"
    elif sum(sell_conditions) >= 3:
        return "DOWN"
    
    return None
```

### 信号强度计算

```python
def _calculate_signal_strength(self, indicators: TechnicalIndicators, 
                              direction: str) -> tuple[str, float]:
    """计算信号置信度和概率。"""
    strength_score = 0.0
    max_score = 0.0
    
    # RSI强度评分
    if indicators.rsi:
        if direction == "UP":
            rsi_strength = max(0, (30 - indicators.rsi) / 30)
        else:
            rsi_strength = max(0, (indicators.rsi - 70) / 30)
        strength_score += rsi_strength * 25  # 最大25分
        max_score += 25
    
    # 趋势强度评分
    trend_strength = indicators.custom.get('my_indicator', 0)
    normalized_trend = min(abs(trend_strength) / self.threshold_value, 1.0)
    strength_score += normalized_trend * 25  # 最大25分
    max_score += 25
    
    # 波动率评分
    if indicators.volatility:
        vol_score = min(indicators.volatility * 1000, 25)  # 最大25分
        strength_score += vol_score
        max_score += 25
    
    # 成交量评分
    volume_score = 25 if self._check_volume_confirmation(indicators) else 0
    strength_score += volume_score
    max_score += 25
    
    # 计算最终评分
    if max_score > 0:
        normalized_score = strength_score / max_score
    else:
        normalized_score = 0.5
    
    # 确定置信度等级
    if normalized_score >= 0.8:
        confidence = "HIGH"
        probability = 0.75 + (normalized_score - 0.8) * 0.5
    elif normalized_score >= 0.6:
        confidence = "MEDIUM"
        probability = 0.60 + (normalized_score - 0.6) * 0.75
    else:
        confidence = "LOW"
        probability = 0.50 + normalized_score * 0.17
    
    return confidence, min(probability, 0.95)
```

## 策略配置管理

### 配置参数类型

```python
class AdvancedStrategyConfig(StrategyConfig):
    def __init__(self, **kwargs):
        default_params = {
            # 技术指标参数
            "sma_short_period": 5,
            "sma_long_period": 20,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            
            # 信号生成参数
            "min_signal_strength": 0.6,
            "confirmation_periods": 2,
            "signal_cooldown_minutes": 15,
            
            # 风险管理参数
            "max_risk_per_trade": 0.02,  # 2%
            "max_daily_trades": 10,
            "stop_loss_pct": 0.05,  # 5%
            
            # 市场条件过滤
            "min_volatility": 0.01,
            "max_volatility": 0.05,
            "trading_hours_only": True,
            
            # 自定义参数
            "custom_threshold": 1.5,
            "enable_volume_filter": True
        }
        
        # 参数验证
        if 'parameters' in kwargs:
            user_params = kwargs['parameters']
            
            # 验证参数范围
            if 'max_risk_per_trade' in user_params:
                if not 0 < user_params['max_risk_per_trade'] <= 0.1:
                    raise ValueError("max_risk_per_trade must be between 0 and 0.1")
            
            if 'rsi_period' in user_params:
                if not 5 <= user_params['rsi_period'] <= 50:
                    raise ValueError("rsi_period must be between 5 and 50")
            
            default_params.update(user_params)
        
        kwargs['parameters'] = default_params
        super().__init__(**kwargs)
```

### 动态配置更新

```python
def update_parameters(self, new_params: dict):
    """动态更新策略参数。"""
    for key, value in new_params.items():
        if key in self.config.parameters:
            self.config.parameters[key] = value
            # 更新实例变量
            if hasattr(self, key):
                setattr(self, key, value)
    
    # 重新验证配置
    self.config.validate()
```

## 风险管理

### 内置风险控制

```python
def _assess_risk_level(self, indicators: TechnicalIndicators) -> str:
    """评估交易风险等级。"""
    risk_factors = 0
    
    # 波动率风险
    if indicators.volatility and indicators.volatility > 0.04:
        risk_factors += 1
    
    # RSI极值风险
    if indicators.rsi:
        if indicators.rsi > 85 or indicators.rsi < 15:
            risk_factors += 1
    
    # 成交量异常风险
    if not self._check_volume_confirmation(indicators):
        risk_factors += 1
    
    # 市场时间风险
    if self._is_market_closed():
        risk_factors += 2
    
    if risk_factors >= 3:
        return "HIGH"
    elif risk_factors >= 2:
        return "MEDIUM"
    else:
        return "LOW"

def validate_signal_conditions(self, signal: StrategySignal) -> bool:
    """验证信号是否满足风险管理条件。"""
    # 调用父类验证
    if not super().validate_signal_conditions(signal):
        return False
    
    # 自定义风险检查
    if signal.risk_level == "HIGH" and signal.confidence != "HIGH":
        return False
    
    # 检查信号冷却时间
    if self._last_signal_time:
        time_diff = (signal.timestamp - self._last_signal_time).total_seconds() / 60
        if time_diff < self.config.parameters.get('signal_cooldown_minutes', 0):
            return False
    
    # 检查每日交易限制
    daily_signals = self._count_daily_signals(signal.timestamp)
    if daily_signals >= self.config.parameters.get('max_daily_trades', float('inf')):
        return False
    
    return True
```

## 策略测试

### 单元测试示例

```python
import unittest
from datetime import datetime
from decimal import Decimal

class TestMyCustomStrategy(unittest.TestCase):
    def setUp(self):
        self.config = MyStrategyConfig(
            parameters={
                "indicator_period": 10,
                "threshold_value": 0.01
            }
        )
        self.strategy = MyCustomStrategy(self.config)
    
    def test_signal_generation(self):
        # 创建测试数据
        test_data = [
            HistoricalDataPoint(
                timestamp=datetime.now(),
                symbol="BTCUSDT",
                close_price=Decimal('50000.00'),
                volume=Decimal('1000')
            )
            # 添加更多测试数据...
        ]
        
        # 测试信号生成
        for data_point in test_data:
            signal = await self.strategy.generate_signal(data_point)
            if signal:
                self.assertIn(signal.direction, ["UP", "DOWN"])
                self.assertIn(signal.confidence, ["LOW", "MEDIUM", "HIGH"])
                self.assertGreaterEqual(signal.probability, 0.5)
                self.assertLessEqual(signal.probability, 1.0)
    
    def test_indicator_calculation(self):
        # 添加测试数据
        for i in range(20):
            data_point = HistoricalDataPoint(
                timestamp=datetime.now(),
                symbol="BTCUSDT",
                close_price=Decimal(f'{50000 + i * 100}'),
                volume=Decimal('1000')
            )
            self.strategy.update_data(data_point)
        
        # 测试指标计算
        indicators = self.strategy.get_indicators()
        self.assertIsNotNone(indicators.sma_20)
        self.assertIsNotNone(indicators.rsi)
        self.assertIsInstance(indicators.custom, dict)
```

### 回测验证

```python
async def backtest_strategy():
    """策略回测示例。"""
    from backtesting.src.strategy_simulator import StrategySimulator, StrategyConfig as SimConfig
    
    # 创建策略实例
    strategy = MyCustomStrategy()
    
    # 配置回测参数
    sim_config = SimConfig(
        initial_balance=Decimal('10000'),
        bet_amount=Decimal('100'),
        symbols=['BTCUSDT'],
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31)
    )
    
    # 运行回测
    simulator = StrategySimulator(sim_config)
    results = await simulator.run_simulation([strategy])
    
    # 分析结果
    for result in results:
        print(f"策略: {result.strategy_name}")
        print(f"总收益: {result.total_return:.2%}")
        print(f"胜率: {result.win_rate:.2%}")
        print(f"最大回撤: {result.max_drawdown:.2%}")
        print(f"夏普比率: {result.sharpe_ratio:.2f}")
```

## 最佳实践

### 1. 代码组织

```python
# 推荐的文件结构
strategies/
├── __init__.py
├── base_strategy.py
├── my_strategy/
│   ├── __init__.py
│   ├── strategy.py          # 主策略类
│   ├── config.py           # 配置类
│   ├── indicators.py       # 自定义指标
│   ├── utils.py           # 工具函数
│   └── tests/
│       ├── test_strategy.py
│       └── test_indicators.py
```

### 2. 性能优化

```python
# 使用缓存避免重复计算
from functools import lru_cache

class OptimizedStrategy(BaseStrategy):
    @lru_cache(maxsize=100)
    def _calculate_expensive_indicator(self, period: int, data_hash: str) -> float:
        """缓存昂贵的指标计算。"""
        # 复杂计算逻辑
        pass
    
    def calculate_indicators(self, data_point: HistoricalDataPoint) -> TechnicalIndicators:
        # 创建数据哈希用于缓存
        data_hash = hash(tuple(float(dp.close_price) for dp in self._price_history[-20:]))
        
        indicators = TechnicalIndicators()
        indicators.custom['expensive_indicator'] = self._calculate_expensive_indicator(20, str(data_hash))
        
        return indicators
```

### 3. 错误处理

```python
def calculate_indicators(self, data_point: HistoricalDataPoint) -> TechnicalIndicators:
    indicators = TechnicalIndicators()
    
    try:
        # 安全的指标计算
        indicators.sma_20 = self._calculate_sma(20)
    except Exception as e:
        self.logger.warning(f"SMA calculation failed: {e}")
        indicators.sma_20 = None
    
    try:
        indicators.rsi = self._calculate_rsi(14)
    except (ZeroDivisionError, ValueError) as e:
        self.logger.warning(f"RSI calculation failed: {e}")
        indicators.rsi = None
    
    return indicators
```

### 4. 日志记录

```python
import logging

class LoggingStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    async def generate_signal(self, data_point: HistoricalDataPoint) -> Optional[StrategySignal]:
        self.logger.debug(f"Processing data point: {data_point.timestamp} - {data_point.close_price}")
        
        signal = await super().generate_signal(data_point)
        
        if signal:
            self.logger.info(f"Generated {signal.direction} signal with {signal.confidence} confidence")
        
        return signal
```

## 常见问题

### Q1: 如何处理数据不足的情况？

```python
def generate_signal(self, data_point: HistoricalDataPoint) -> Optional[StrategySignal]:
    # 检查最小数据要求
    min_required = max(self.sma_period, self.rsi_period) + 5
    if len(self._price_history) < min_required:
        self.logger.debug(f"Insufficient data: {len(self._price_history)} < {min_required}")
        return None
    
    # 继续处理...
```

### Q2: 如何避免过度拟合？

- 使用简单的指标组合
- 在不同时间段测试策略
- 实施交叉验证
- 避免过多的参数优化

### Q3: 如何处理市场异常情况？

```python
def _check_market_conditions(self, indicators: TechnicalIndicators) -> bool:
    """检查市场是否适合交易。"""
    # 检查极端波动率
    if indicators.volatility and indicators.volatility > 0.1:  # 10%
        return False
    
    # 检查流动性
    if indicators.volume_ratio and indicators.volume_ratio < 0.1:
        return False
    
    # 检查价格跳空
    if len(self._price_history) >= 2:
        current_price = float(self._price_history[-1].close_price)
        prev_price = float(self._price_history[-2].close_price)
        price_gap = abs(current_price - prev_price) / prev_price
        if price_gap > 0.05:  # 5% 跳空
            return False
    
    return True
```

### Q4: 如何优化策略参数？

```python
from itertools import product

def optimize_parameters(strategy_class, data, param_ranges):
    """参数优化示例。"""
    best_params = None
    best_score = -float('inf')
    
    # 生成参数组合
    param_combinations = list(product(*param_ranges.values()))
    
    for params in param_combinations:
        # 创建参数字典
        param_dict = dict(zip(param_ranges.keys(), params))
        
        # 创建策略实例
        config = MyStrategyConfig(parameters=param_dict)
        strategy = strategy_class(config)
        
        # 运行回测
        score = run_backtest(strategy, data)
        
        # 更新最佳参数
        if score > best_score:
            best_score = score
            best_params = param_dict
    
    return best_params, best_score
```

## 总结

创建成功的交易策略需要：

1. **清晰的逻辑**: 明确的入场和出场条件
2. **严格的测试**: 充分的历史数据验证
3. **风险管理**: 完善的风险控制机制
4. **持续优化**: 根据市场变化调整策略
5. **代码质量**: 可维护和可扩展的代码结构

遵循本指南的最佳实践，你将能够创建出稳健、高效的交易策略。记住，没有完美的策略，关键是要在风险和收益之间找到平衡。