#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略使用示例

展示完整的策略开发到回测流程，包括：
1. 创建自定义策略
2. 配置策略参数
3. 运行策略测试
4. 执行回测
5. 分析结果
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List

# 导入必要的模块
from backtesting.src.strategies.base_strategy import (
    BaseStrategy, StrategyConfig, StrategySignal, TechnicalIndicators
)
from backtesting.src.loaders.data_loader import HistoricalDataPoint
from backtesting.src.strategy_simulator import StrategySimulator, StrategyConfig as SimConfig
from backtesting.src.testing.strategy_tester import run_strategy_tests
from backtesting.src.strategies.momentum_strategy import MomentumStrategy, MomentumStrategyConfig
from backtesting.src.strategies.mean_reversion_strategy import MeanReversionStrategy, MeanReversionStrategyConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# 示例1: 创建自定义策略
# ============================================================================

class CustomTrendStrategyConfig(StrategyConfig):
    """自定义趋势策略配置。"""
    
    def __init__(self, **kwargs):
        default_params = {
            "short_ma_period": 5,
            "long_ma_period": 20,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "trend_strength_threshold": 0.02,
            "volume_confirmation": True,
            "min_volume_ratio": 1.2
        }
        
        if 'parameters' in kwargs:
            default_params.update(kwargs['parameters'])
        kwargs['parameters'] = default_params
        
        kwargs.setdefault('name', 'CustomTrendStrategy')
        kwargs.setdefault('description', '基于移动平均和RSI的趋势跟踪策略')
        kwargs.setdefault('min_confidence', 'MEDIUM')
        kwargs.setdefault('min_probability', 0.65)
        
        super().__init__(**kwargs)


class CustomTrendStrategy(BaseStrategy):
    """自定义趋势策略示例。"""
    
    def __init__(self, config: Optional[CustomTrendStrategyConfig] = None):
        if config is None:
            config = CustomTrendStrategyConfig()
        super().__init__(config)
        
        # 提取策略参数
        params = self.config.parameters
        self.short_ma_period = params['short_ma_period']
        self.long_ma_period = params['long_ma_period']
        self.rsi_period = params['rsi_period']
        self.rsi_overbought = params['rsi_overbought']
        self.rsi_oversold = params['rsi_oversold']
        self.trend_strength_threshold = params['trend_strength_threshold']
        self.volume_confirmation = params['volume_confirmation']
        self.min_volume_ratio = params['min_volume_ratio']
    
    async def generate_signal(self, data_point: HistoricalDataPoint) -> Optional[StrategySignal]:
        """生成交易信号。"""
        # 更新数据
        self.update_data(data_point)
        
        # 检查数据充足性
        min_required = max(self.short_ma_period, self.long_ma_period, self.rsi_period) + 5
        if len(self._price_history) < min_required:
            return None
        
        # 计算技术指标
        indicators = self.get_indicators()
        if not indicators:
            return None
        
        # 分析趋势方向
        signal_direction = self._analyze_trend(indicators, data_point)
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
        """计算技术指标。"""
        indicators = TechnicalIndicators()
        
        # 计算移动平均线
        indicators.sma_5 = self._calculate_sma(self.short_ma_period)
        indicators.sma_20 = self._calculate_sma(self.long_ma_period)
        
        # 计算RSI
        indicators.rsi = self._calculate_rsi(self.rsi_period)
        
        # 计算波动率
        indicators.volatility = self._calculate_volatility(20)
        
        # 计算成交量比率
        indicators.volume_ratio = self._calculate_volume_ratio(10)
        
        # 自定义指标
        indicators.custom = {
            'trend_strength': self._calculate_trend_strength(),
            'ma_cross_signal': self._calculate_ma_cross_signal(),
            'price_position': self._calculate_price_position(data_point)
        }
        
        return indicators
    
    def _analyze_trend(self, indicators: TechnicalIndicators, data_point: HistoricalDataPoint) -> Optional[str]:
        """分析趋势方向。"""
        current_price = float(data_point.close_price)
        
        # 移动平均交叉信号
        ma_cross = indicators.custom.get('ma_cross_signal', 0)
        
        # RSI条件
        rsi_bullish = indicators.rsi and indicators.rsi < self.rsi_overbought
        rsi_bearish = indicators.rsi and indicators.rsi > self.rsi_oversold
        
        # 趋势强度
        trend_strength = indicators.custom.get('trend_strength', 0)
        
        # 价格位置
        price_position = indicators.custom.get('price_position', 0)
        
        # 成交量确认
        volume_ok = True
        if self.volume_confirmation:
            volume_ok = indicators.volume_ratio and indicators.volume_ratio >= self.min_volume_ratio
        
        # 买入条件
        buy_conditions = [
            ma_cross > 0,  # 短期均线上穿长期均线
            rsi_bullish,   # RSI不在超买区域
            trend_strength > self.trend_strength_threshold,  # 趋势强度足够
            price_position > 0,  # 价格在均线上方
            volume_ok      # 成交量确认
        ]
        
        # 卖出条件
        sell_conditions = [
            ma_cross < 0,  # 短期均线下穿长期均线
            rsi_bearish,   # RSI不在超卖区域
            trend_strength < -self.trend_strength_threshold,  # 趋势强度足够
            price_position < 0,  # 价格在均线下方
            volume_ok      # 成交量确认
        ]
        
        # 判断信号方向
        if sum(buy_conditions) >= 4:
            return "UP"
        elif sum(sell_conditions) >= 4:
            return "DOWN"
        
        return None
    
    def _calculate_trend_strength(self) -> float:
        """计算趋势强度。"""
        if len(self._price_history) < 10:
            return 0.0
        
        prices = [float(dp.close_price) for dp in self._price_history[-10:]]
        
        # 计算价格变化率
        price_changes = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        # 计算趋势一致性
        positive_changes = sum(1 for change in price_changes if change > 0)
        negative_changes = sum(1 for change in price_changes if change < 0)
        
        # 计算平均变化率
        avg_change = sum(price_changes) / len(price_changes)
        
        # 趋势强度 = 方向一致性 * 平均变化率
        if positive_changes > negative_changes:
            consistency = positive_changes / len(price_changes)
        else:
            consistency = -negative_changes / len(price_changes)
        
        return consistency * avg_change
    
    def _calculate_ma_cross_signal(self) -> float:
        """计算移动平均交叉信号。"""
        if len(self._price_history) < max(self.short_ma_period, self.long_ma_period) + 1:
            return 0.0
        
        # 当前移动平均值
        current_short_ma = self._calculate_sma(self.short_ma_period)
        current_long_ma = self._calculate_sma(self.long_ma_period)
        
        if not current_short_ma or not current_long_ma:
            return 0.0
        
        # 前一期移动平均值
        prev_prices = self._price_history[:-1]
        if len(prev_prices) < max(self.short_ma_period, self.long_ma_period):
            return 0.0
        
        prev_short_prices = [float(dp.close_price) for dp in prev_prices[-self.short_ma_period:]]
        prev_long_prices = [float(dp.close_price) for dp in prev_prices[-self.long_ma_period:]]
        
        prev_short_ma = sum(prev_short_prices) / len(prev_short_prices)
        prev_long_ma = sum(prev_long_prices) / len(prev_long_prices)
        
        # 计算交叉信号
        current_diff = current_short_ma - current_long_ma
        prev_diff = prev_short_ma - prev_long_ma
        
        # 返回交叉强度
        return current_diff - prev_diff
    
    def _calculate_price_position(self, data_point: HistoricalDataPoint) -> float:
        """计算价格相对于均线的位置。"""
        current_price = float(data_point.close_price)
        long_ma = self._calculate_sma(self.long_ma_period)
        
        if not long_ma:
            return 0.0
        
        return (current_price - long_ma) / long_ma
    
    def _calculate_signal_strength(self, indicators: TechnicalIndicators, direction: str) -> tuple[str, float]:
        """计算信号强度。"""
        strength_score = 0.0
        max_score = 0.0
        
        # RSI强度评分
        if indicators.rsi:
            if direction == "UP":
                rsi_strength = max(0, (50 - indicators.rsi) / 50) if indicators.rsi < 50 else 0
            else:
                rsi_strength = max(0, (indicators.rsi - 50) / 50) if indicators.rsi > 50 else 0
            strength_score += rsi_strength * 25
            max_score += 25
        
        # 趋势强度评分
        trend_strength = abs(indicators.custom.get('trend_strength', 0))
        normalized_trend = min(trend_strength / self.trend_strength_threshold, 1.0)
        strength_score += normalized_trend * 30
        max_score += 30
        
        # 移动平均交叉强度
        ma_cross = abs(indicators.custom.get('ma_cross_signal', 0))
        normalized_cross = min(ma_cross * 1000, 20)  # 归一化
        strength_score += normalized_cross
        max_score += 20
        
        # 成交量确认
        if indicators.volume_ratio and indicators.volume_ratio >= self.min_volume_ratio:
            volume_score = min((indicators.volume_ratio - 1) * 25, 25)
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
            probability = 0.65 + (normalized_score - 0.6) * 0.5
        else:
            confidence = "LOW"
            probability = 0.55 + normalized_score * 0.17
        
        return confidence, min(probability, 0.95)


# ============================================================================
# 示例2: 策略测试
# ============================================================================

def test_custom_strategy():
    """测试自定义策略。"""
    logger.info("开始测试自定义策略...")
    
    # 创建策略实例
    config = CustomTrendStrategyConfig(
        parameters={
            "short_ma_period": 5,
            "long_ma_period": 15,
            "rsi_period": 14,
            "trend_strength_threshold": 0.015
        }
    )
    strategy = CustomTrendStrategy(config)
    
    # 运行测试
    test_report = run_strategy_tests(strategy, save_report=True)
    
    # 打印测试结果
    logger.info(f"策略测试完成: {strategy.name}")
    logger.info(f"测试通过率: {test_report['summary']['success_rate']:.2%}")
    
    for result in test_report['test_results']:
        status = "✓" if result['passed'] else "✗"
        logger.info(f"{status} {result['test_name']}: {result['message']}")
    
    return test_report


# ============================================================================
# 示例3: 策略回测
# ============================================================================

async def run_strategy_backtest():
    """运行策略回测。"""
    logger.info("开始策略回测...")
    
    # 创建多个策略进行对比
    strategies = [
        # 自定义策略
        CustomTrendStrategy(CustomTrendStrategyConfig(
            parameters={"trend_strength_threshold": 0.01}
        )),
        
        # 动量策略
        MomentumStrategy(MomentumStrategyConfig(
            parameters={"rsi_period": 10, "momentum_threshold": 0.02}
        )),
        
        # 均值回归策略
        MeanReversionStrategy(MeanReversionStrategyConfig(
            parameters={"bollinger_period": 15, "rsi_oversold": 25}
        ))
    ]
    
    # 配置回测参数
    sim_config = SimConfig(
        initial_balance=Decimal('10000'),
        bet_amount=Decimal('100'),
        symbols=['BTCUSDT', 'ETHUSDT'],
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now() - timedelta(days=1),
        contract_duration_minutes=5,
        payout_rate=Decimal('0.85'),
        max_concurrent_contracts=5
    )
    
    # 运行回测
    simulator = StrategySimulator(sim_config)
    results = await simulator.run_simulation(strategies)
    
    # 分析结果
    logger.info("\n" + "="*60)
    logger.info("回测结果分析")
    logger.info("="*60)
    
    for result in results:
        logger.info(f"\n策略: {result.strategy_name}")
        logger.info(f"总收益: {result.total_return:.2%}")
        logger.info(f"胜率: {result.win_rate:.2%}")
        logger.info(f"总交易数: {result.total_trades}")
        logger.info(f"盈利交易: {result.winning_trades}")
        logger.info(f"亏损交易: {result.losing_trades}")
        logger.info(f"最大回撤: {result.max_drawdown:.2%}")
        logger.info(f"夏普比率: {result.sharpe_ratio:.2f}")
        logger.info(f"最终余额: ${result.final_balance}")
        
        # 按交易对分析
        if result.symbol_performance:
            logger.info("\n按交易对表现:")
            for symbol, perf in result.symbol_performance.items():
                logger.info(f"  {symbol}: 收益率 {perf['return']:.2%}, 胜率 {perf['win_rate']:.2%}")
    
    return results


# ============================================================================
# 示例4: 策略优化
# ============================================================================

async def optimize_strategy_parameters():
    """策略参数优化示例。"""
    logger.info("开始策略参数优化...")
    
    # 定义参数范围
    param_ranges = {
        'short_ma_period': [3, 5, 7, 10],
        'long_ma_period': [15, 20, 25, 30],
        'rsi_period': [10, 14, 18, 21],
        'trend_strength_threshold': [0.005, 0.01, 0.015, 0.02]
    }
    
    best_params = None
    best_return = -float('inf')
    optimization_results = []
    
    # 遍历参数组合
    from itertools import product
    
    param_combinations = list(product(*param_ranges.values()))
    total_combinations = len(param_combinations)
    
    logger.info(f"总共需要测试 {total_combinations} 个参数组合")
    
    for i, params in enumerate(param_combinations):
        # 创建参数字典
        param_dict = dict(zip(param_ranges.keys(), params))
        
        logger.info(f"测试参数组合 {i+1}/{total_combinations}: {param_dict}")
        
        try:
            # 创建策略
            config = CustomTrendStrategyConfig(parameters=param_dict)
            strategy = CustomTrendStrategy(config)
            
            # 运行简化回测
            sim_config = SimConfig(
                initial_balance=Decimal('10000'),
                bet_amount=Decimal('100'),
                symbols=['BTCUSDT'],
                start_date=datetime.now() - timedelta(days=7),
                end_date=datetime.now() - timedelta(days=1),
                contract_duration_minutes=5
            )
            
            simulator = StrategySimulator(sim_config)
            results = await simulator.run_simulation([strategy])
            
            if results:
                result = results[0]
                total_return = float(result.total_return)
                
                optimization_results.append({
                    'parameters': param_dict,
                    'total_return': total_return,
                    'win_rate': float(result.win_rate),
                    'total_trades': result.total_trades,
                    'sharpe_ratio': float(result.sharpe_ratio)
                })
                
                # 更新最佳参数
                if total_return > best_return:
                    best_return = total_return
                    best_params = param_dict
                    logger.info(f"发现更好的参数组合! 收益率: {total_return:.2%}")
        
        except Exception as e:
            logger.error(f"参数组合测试失败: {e}")
    
    # 输出优化结果
    logger.info("\n" + "="*60)
    logger.info("参数优化结果")
    logger.info("="*60)
    
    if best_params:
        logger.info(f"最佳参数组合: {best_params}")
        logger.info(f"最佳收益率: {best_return:.2%}")
        
        # 显示前5个最佳结果
        sorted_results = sorted(optimization_results, key=lambda x: x['total_return'], reverse=True)
        logger.info("\n前5个最佳参数组合:")
        for i, result in enumerate(sorted_results[:5]):
            logger.info(f"{i+1}. 收益率: {result['total_return']:.2%}, 胜率: {result['win_rate']:.2%}, 参数: {result['parameters']}")
    
    return optimization_results


# ============================================================================
# 示例5: 实时策略监控
# ============================================================================

class StrategyMonitor:
    """策略实时监控。"""
    
    def __init__(self, strategies: List[BaseStrategy]):
        self.strategies = strategies
        self.running = False
        self.signals_history = []
    
    async def start_monitoring(self, duration_minutes: int = 60):
        """开始监控策略。"""
        logger.info(f"开始监控 {len(self.strategies)} 个策略，持续 {duration_minutes} 分钟")
        
        self.running = True
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        while self.running and datetime.now() < end_time:
            # 模拟实时数据（实际应用中从数据源获取）
            current_data = self._generate_mock_data()
            
            # 为每个策略生成信号
            for strategy in self.strategies:
                try:
                    signal = await strategy.generate_signal(current_data)
                    if signal:
                        self._handle_signal(signal)
                except Exception as e:
                    logger.error(f"策略 {strategy.name} 信号生成失败: {e}")
            
            # 等待下一个周期
            await asyncio.sleep(60)  # 1分钟间隔
        
        logger.info("策略监控结束")
        self._generate_monitoring_report()
    
    def _generate_mock_data(self) -> HistoricalDataPoint:
        """生成模拟数据。"""
        import random
        
        base_price = 50000
        price_change = random.uniform(-0.02, 0.02)  # ±2%变化
        current_price = base_price * (1 + price_change)
        
        return HistoricalDataPoint(
            timestamp=datetime.now(),
            symbol="BTCUSDT",
            close_price=Decimal(str(round(current_price, 2))),
            volume=Decimal(str(random.randint(1000, 5000)))
        )
    
    def _handle_signal(self, signal: StrategySignal):
        """处理信号。"""
        self.signals_history.append(signal)
        
        logger.info(
            f"收到信号 - 策略: {signal.strategy_name}, "
            f"方向: {signal.direction}, 置信度: {signal.confidence}, "
            f"概率: {signal.probability:.2%}"
        )
    
    def _generate_monitoring_report(self):
        """生成监控报告。"""
        logger.info("\n" + "="*60)
        logger.info("策略监控报告")
        logger.info("="*60)
        
        # 按策略统计信号
        strategy_stats = {}
        for signal in self.signals_history:
            name = signal.strategy_name
            if name not in strategy_stats:
                strategy_stats[name] = {'total': 0, 'up': 0, 'down': 0, 'high_conf': 0}
            
            strategy_stats[name]['total'] += 1
            if signal.direction == 'UP':
                strategy_stats[name]['up'] += 1
            else:
                strategy_stats[name]['down'] += 1
            
            if signal.confidence == 'HIGH':
                strategy_stats[name]['high_conf'] += 1
        
        for strategy_name, stats in strategy_stats.items():
            logger.info(f"\n策略: {strategy_name}")
            logger.info(f"  总信号数: {stats['total']}")
            logger.info(f"  看涨信号: {stats['up']} ({stats['up']/stats['total']:.1%})")
            logger.info(f"  看跌信号: {stats['down']} ({stats['down']/stats['total']:.1%})")
            logger.info(f"  高置信度: {stats['high_conf']} ({stats['high_conf']/stats['total']:.1%})")
    
    def stop_monitoring(self):
        """停止监控。"""
        self.running = False


# ============================================================================
# 主函数 - 完整示例流程
# ============================================================================

async def main():
    """主函数 - 展示完整的策略开发到回测流程。"""
    logger.info("开始策略开发到回测完整流程演示")
    
    try:
        # 步骤1: 测试自定义策略
        logger.info("\n" + "="*60)
        logger.info("步骤1: 策略测试")
        logger.info("="*60)
        test_report = test_custom_strategy()
        
        # 步骤2: 运行回测
        logger.info("\n" + "="*60)
        logger.info("步骤2: 策略回测")
        logger.info("="*60)
        backtest_results = await run_strategy_backtest()
        
        # 步骤3: 参数优化（可选，耗时较长）
        logger.info("\n" + "="*60)
        logger.info("步骤3: 参数优化（简化版）")
        logger.info("="*60)
        # optimization_results = await optimize_strategy_parameters()
        logger.info("参数优化已跳过（耗时较长），如需运行请取消注释")
        
        # 步骤4: 实时监控演示
        logger.info("\n" + "="*60)
        logger.info("步骤4: 实时监控演示（5分钟）")
        logger.info("="*60)
        
        strategies = [
            CustomTrendStrategy(),
            MomentumStrategy()
        ]
        
        monitor = StrategyMonitor(strategies)
        await monitor.start_monitoring(duration_minutes=5)
        
        logger.info("\n" + "="*60)
        logger.info("完整流程演示结束")
        logger.info("="*60)
        
        # 总结
        logger.info("\n流程总结:")
        logger.info("1. ✓ 创建了自定义趋势策略")
        logger.info("2. ✓ 运行了策略测试验证")
        logger.info("3. ✓ 执行了多策略回测对比")
        logger.info("4. ✓ 演示了实时监控功能")
        logger.info("\n你现在可以:")
        logger.info("- 根据回测结果调整策略参数")
        logger.info("- 添加更多技术指标和过滤条件")
        logger.info("- 实施风险管理规则")
        logger.info("- 部署到生产环境进行实盘交易")
        
    except Exception as e:
        logger.error(f"流程执行出错: {e}")
        raise


if __name__ == "__main__":
    # 运行完整示例
    asyncio.run(main())