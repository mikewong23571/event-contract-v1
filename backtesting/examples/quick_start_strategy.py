#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略快速入门示例

这是一个简化的示例，展示如何快速创建和测试一个交易策略。
适合初学者快速上手。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

# 导入必要的模块
from backtesting.src.strategies.base_strategy import (
    BaseStrategy, StrategyConfig, StrategySignal, TechnicalIndicators
)
from backtesting.src.loaders.data_loader import HistoricalDataPoint
from backtesting.src.strategy_simulator import StrategySimulator, StrategyConfig as SimConfig
from backtesting.src.testing.strategy_tester import run_strategy_tests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 简单策略示例
# ============================================================================

class SimpleStrategyConfig(StrategyConfig):
    """简单策略配置。"""
    
    def __init__(self, **kwargs):
        # 设置默认参数
        default_params = {
            "ma_period": 10,        # 移动平均周期
            "price_threshold": 0.01  # 价格阈值（1%）
        }
        
        if 'parameters' in kwargs:
            default_params.update(kwargs['parameters'])
        kwargs['parameters'] = default_params
        
        # 设置策略基本信息
        kwargs.setdefault('name', 'SimpleStrategy')
        kwargs.setdefault('description', '基于移动平均的简单策略')
        
        super().__init__(**kwargs)


class SimpleStrategy(BaseStrategy):
    """简单策略 - 基于移动平均线的交易策略。"""
    
    def __init__(self, config: Optional[SimpleStrategyConfig] = None):
        if config is None:
            config = SimpleStrategyConfig()
        super().__init__(config)
        
        # 获取策略参数
        self.ma_period = self.config.parameters['ma_period']
        self.price_threshold = self.config.parameters['price_threshold']
    
    async def generate_signal(self, data_point: HistoricalDataPoint) -> Optional[StrategySignal]:
        """生成交易信号。"""
        # 更新数据
        self.update_data(data_point)
        
        # 检查是否有足够的历史数据
        if len(self._price_history) < self.ma_period + 2:
            return None
        
        # 计算技术指标
        indicators = self.get_indicators()
        if not indicators or not indicators.sma_10:
            return None
        
        # 简单的交易逻辑
        current_price = float(data_point.close_price)
        ma_value = indicators.sma_10
        
        # 计算价格相对于移动平均线的偏离
        price_deviation = (current_price - ma_value) / ma_value
        
        # 生成信号
        signal_direction = None
        confidence = "LOW"
        probability = 0.55
        
        if price_deviation > self.price_threshold:
            # 价格显著高于移动平均线，预期回调
            signal_direction = "DOWN"
            confidence = "MEDIUM" if abs(price_deviation) > self.price_threshold * 2 else "LOW"
            probability = 0.60 + min(abs(price_deviation) * 10, 0.15)
        elif price_deviation < -self.price_threshold:
            # 价格显著低于移动平均线，预期反弹
            signal_direction = "UP"
            confidence = "MEDIUM" if abs(price_deviation) > self.price_threshold * 2 else "LOW"
            probability = 0.60 + min(abs(price_deviation) * 10, 0.15)
        
        if not signal_direction:
            return None
        
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
            signal_reason=f"价格偏离移动平均线 {price_deviation:.2%}",
            conditions_met=[f"价格偏离: {price_deviation:.2%}", f"移动平均: {ma_value:.2f}"],
            risk_level="LOW"
        )
        
        # 验证信号
        if not self.validate_signal_conditions(signal):
            return None
        
        self._signals_generated += 1
        self._last_signal_time = data_point.timestamp
        
        return signal
    
    def calculate_indicators(self, data_point: HistoricalDataPoint) -> TechnicalIndicators:
        """计算技术指标。"""
        indicators = TechnicalIndicators()
        
        # 计算移动平均线
        indicators.sma_10 = self._calculate_sma(self.ma_period)
        
        # 计算价格变化
        indicators.price_change = self._calculate_price_change(1)
        
        return indicators


# ============================================================================
# 快速测试函数
# ============================================================================

def quick_test():
    """快速测试策略。"""
    logger.info("开始快速测试...")
    
    # 创建策略
    strategy = SimpleStrategy()
    
    # 运行测试
    test_report = run_strategy_tests(strategy, save_report=False)
    
    # 显示结果
    success_rate = test_report['summary']['success_rate']
    logger.info(f"测试完成! 通过率: {success_rate:.1%}")
    
    if success_rate >= 0.8:
        logger.info("✓ 策略测试通过，可以进行回测")
        return True
    else:
        logger.warning("✗ 策略测试未完全通过，建议检查实现")
        return False


async def quick_backtest():
    """快速回测。"""
    logger.info("开始快速回测...")
    
    # 创建策略
    strategy = SimpleStrategy(SimpleStrategyConfig(
        parameters={
            "ma_period": 10,
            "price_threshold": 0.015  # 1.5%
        }
    ))
    
    # 配置回测
    sim_config = SimConfig(
        initial_balance=Decimal('1000'),
        bet_amount=Decimal('50'),
        symbols=['BTCUSDT'],
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now() - timedelta(days=1),
        contract_duration_minutes=5
    )
    
    # 运行回测
    simulator = StrategySimulator(sim_config)
    results = await simulator.run_simulation([strategy])
    
    # 显示结果
    if results:
        result = results[0]
        logger.info(f"\n回测结果:")
        logger.info(f"总收益: {result.total_return:.2%}")
        logger.info(f"胜率: {result.win_rate:.1%}")
        logger.info(f"总交易: {result.total_trades}")
        logger.info(f"最终余额: ${result.final_balance}")
        
        if result.total_return > 0:
            logger.info("✓ 策略盈利!")
        else:
            logger.info("✗ 策略亏损")
    
    return results


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """主函数 - 快速入门流程。"""
    logger.info("=" * 50)
    logger.info("策略快速入门示例")
    logger.info("=" * 50)
    
    try:
        # 步骤1: 快速测试
        logger.info("\n步骤1: 策略测试")
        test_passed = quick_test()
        
        if test_passed:
            # 步骤2: 快速回测
            logger.info("\n步骤2: 策略回测")
            results = await quick_backtest()
            
            logger.info("\n" + "=" * 50)
            logger.info("快速入门完成!")
            logger.info("=" * 50)
            logger.info("\n下一步你可以:")
            logger.info("1. 调整策略参数优化表现")
            logger.info("2. 添加更多技术指标")
            logger.info("3. 实施风险管理规则")
            logger.info("4. 查看完整示例: strategy_usage_example.py")
        else:
            logger.info("\n请先修复策略测试问题再进行回测")
    
    except Exception as e:
        logger.error(f"执行出错: {e}")


if __name__ == "__main__":
    # 运行快速入门示例
    asyncio.run(main())