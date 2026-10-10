#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略测试工具

提供策略验证、单元测试、性能测试等功能。
"""

import asyncio
import logging
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import statistics
import json

from backtesting.src.strategies.base_strategy import BaseStrategy, StrategySignal, TechnicalIndicators
from backtesting.src.loaders.data_loader import HistoricalDataPoint
from backtesting.src.strategy_simulator import StrategySimulator, StrategyConfig as SimConfig


@dataclass
class TestResult:
    """测试结果数据类。"""
    test_name: str
    passed: bool
    message: str
    execution_time: float
    details: Dict[str, Any] = None


@dataclass
class PerformanceMetrics:
    """性能指标数据类。"""
    avg_execution_time: float
    max_execution_time: float
    min_execution_time: float
    total_signals: int
    signals_per_second: float
    memory_usage_mb: float


class StrategyTester:
    """策略测试器。"""
    
    def __init__(self, strategy: BaseStrategy, logger: Optional[logging.Logger] = None):
        self.strategy = strategy
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.test_results: List[TestResult] = []
        
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试。"""
        self.logger.info(f"开始测试策略: {self.strategy.name}")
        
        # 清空之前的测试结果
        self.test_results.clear()
        
        # 运行各种测试
        self._test_initialization()
        self._test_data_handling()
        self._test_indicator_calculation()
        self._test_signal_generation()
        self._test_signal_validation()
        self._test_edge_cases()
        self._test_performance()
        
        # 生成测试报告
        return self._generate_test_report()
    
    def _test_initialization(self):
        """测试策略初始化。"""
        try:
            start_time = datetime.now()
            
            # 检查基本属性
            assert hasattr(self.strategy, 'name'), "策略必须有名称"
            assert hasattr(self.strategy, 'version'), "策略必须有版本"
            assert hasattr(self.strategy, 'config'), "策略必须有配置"
            
            # 检查必要方法
            assert callable(getattr(self.strategy, 'generate_signal', None)), "必须实现generate_signal方法"
            assert callable(getattr(self.strategy, 'calculate_indicators', None)), "必须实现calculate_indicators方法"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.test_results.append(TestResult(
                test_name="初始化测试",
                passed=True,
                message="策略初始化正常",
                execution_time=execution_time
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="初始化测试",
                passed=False,
                message=f"初始化失败: {str(e)}",
                execution_time=0
            ))
    
    def _test_data_handling(self):
        """测试数据处理。"""
        try:
            start_time = datetime.now()
            
            # 创建测试数据
            test_data = self._create_test_data(50)
            
            # 测试数据更新
            for data_point in test_data:
                self.strategy.update_data(data_point)
            
            # 检查数据是否正确存储
            assert len(self.strategy._price_history) == len(test_data), "价格历史长度不匹配"
            assert len(self.strategy._volume_history) == len(test_data), "成交量历史长度不匹配"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.test_results.append(TestResult(
                test_name="数据处理测试",
                passed=True,
                message="数据处理正常",
                execution_time=execution_time
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="数据处理测试",
                passed=False,
                message=f"数据处理失败: {str(e)}",
                execution_time=0
            ))
    
    def _test_indicator_calculation(self):
        """测试技术指标计算。"""
        try:
            start_time = datetime.now()
            
            # 准备足够的测试数据
            test_data = self._create_test_data(100)
            for data_point in test_data:
                self.strategy.update_data(data_point)
            
            # 测试指标计算
            indicators = self.strategy.calculate_indicators(test_data[-1])
            
            # 验证指标类型
            assert isinstance(indicators, TechnicalIndicators), "返回的指标类型不正确"
            
            # 检查常用指标
            if indicators.sma_20 is not None:
                assert isinstance(indicators.sma_20, (int, float)), "SMA指标类型不正确"
                assert indicators.sma_20 > 0, "SMA指标值应为正数"
            
            if indicators.rsi is not None:
                assert isinstance(indicators.rsi, (int, float)), "RSI指标类型不正确"
                assert 0 <= indicators.rsi <= 100, "RSI指标值应在0-100之间"
            
            if indicators.volatility is not None:
                assert isinstance(indicators.volatility, (int, float)), "波动率指标类型不正确"
                assert indicators.volatility >= 0, "波动率指标值应为非负数"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.test_results.append(TestResult(
                test_name="指标计算测试",
                passed=True,
                message="指标计算正常",
                execution_time=execution_time,
                details={
                    "sma_20": indicators.sma_20,
                    "rsi": indicators.rsi,
                    "volatility": indicators.volatility
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="指标计算测试",
                passed=False,
                message=f"指标计算失败: {str(e)}",
                execution_time=0
            ))
    
    async def _test_signal_generation(self):
        """测试信号生成。"""
        try:
            start_time = datetime.now()
            
            # 准备测试数据
            test_data = self._create_test_data(100)
            signals_generated = 0
            valid_signals = 0
            
            # 测试信号生成
            for data_point in test_data:
                signal = await self.strategy.generate_signal(data_point)
                
                if signal:
                    signals_generated += 1
                    
                    # 验证信号格式
                    assert isinstance(signal, StrategySignal), "信号类型不正确"
                    assert signal.direction in ["UP", "DOWN"], "信号方向不正确"
                    assert signal.confidence in ["LOW", "MEDIUM", "HIGH"], "信号置信度不正确"
                    assert 0.5 <= signal.probability <= 1.0, "信号概率范围不正确"
                    assert signal.strategy_name == self.strategy.name, "策略名称不匹配"
                    
                    valid_signals += 1
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.test_results.append(TestResult(
                test_name="信号生成测试",
                passed=True,
                message=f"生成了{signals_generated}个信号，其中{valid_signals}个有效",
                execution_time=execution_time,
                details={
                    "total_signals": signals_generated,
                    "valid_signals": valid_signals,
                    "signal_rate": signals_generated / len(test_data) if test_data else 0
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="信号生成测试",
                passed=False,
                message=f"信号生成失败: {str(e)}",
                execution_time=0
            ))
    
    def _test_signal_validation(self):
        """测试信号验证。"""
        try:
            start_time = datetime.now()
            
            # 创建测试信号
            test_signals = [
                # 有效信号
                StrategySignal(
                    timestamp=datetime.now(),
                    symbol="BTCUSDT",
                    direction="UP",
                    confidence="HIGH",
                    probability=0.75,
                    expiry_minutes=5,
                    strategy_name=self.strategy.name,
                    strategy_version=self.strategy.version,
                    indicators=TechnicalIndicators(),
                    entry_price=Decimal('50000'),
                    signal_reason="测试信号",
                    conditions_met=["条件1", "条件2"],
                    risk_level="LOW"
                ),
                # 无效信号（概率过低）
                StrategySignal(
                    timestamp=datetime.now(),
                    symbol="BTCUSDT",
                    direction="DOWN",
                    confidence="LOW",
                    probability=0.45,  # 低于最小要求
                    expiry_minutes=5,
                    strategy_name=self.strategy.name,
                    strategy_version=self.strategy.version,
                    indicators=TechnicalIndicators(),
                    entry_price=Decimal('50000'),
                    signal_reason="测试信号",
                    conditions_met=["条件1"],
                    risk_level="HIGH"
                )
            ]
            
            valid_count = 0
            for signal in test_signals:
                if self.strategy.validate_signal_conditions(signal):
                    valid_count += 1
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 第一个信号应该有效，第二个应该无效
            expected_valid = 1
            
            self.test_results.append(TestResult(
                test_name="信号验证测试",
                passed=valid_count == expected_valid,
                message=f"验证了{len(test_signals)}个信号，{valid_count}个通过验证（期望{expected_valid}个）",
                execution_time=execution_time,
                details={
                    "total_tested": len(test_signals),
                    "valid_signals": valid_count,
                    "expected_valid": expected_valid
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="信号验证测试",
                passed=False,
                message=f"信号验证失败: {str(e)}",
                execution_time=0
            ))
    
    def _test_edge_cases(self):
        """测试边界情况。"""
        try:
            start_time = datetime.now()
            
            edge_cases_passed = 0
            total_edge_cases = 0
            
            # 测试1: 空数据
            total_edge_cases += 1
            try:
                empty_data = HistoricalDataPoint(
                    timestamp=datetime.now(),
                    symbol="BTCUSDT",
                    close_price=Decimal('0'),
                    volume=Decimal('0')
                )
                signal = asyncio.run(self.strategy.generate_signal(empty_data))
                # 应该返回None或处理错误
                edge_cases_passed += 1
            except Exception:
                pass  # 预期可能出错
            
            # 测试2: 极端价格
            total_edge_cases += 1
            try:
                extreme_data = HistoricalDataPoint(
                    timestamp=datetime.now(),
                    symbol="BTCUSDT",
                    close_price=Decimal('999999999'),
                    volume=Decimal('1')
                )
                signal = asyncio.run(self.strategy.generate_signal(extreme_data))
                edge_cases_passed += 1
            except Exception:
                pass
            
            # 测试3: 负价格（应该被拒绝）
            total_edge_cases += 1
            try:
                negative_data = HistoricalDataPoint(
                    timestamp=datetime.now(),
                    symbol="BTCUSDT",
                    close_price=Decimal('-100'),
                    volume=Decimal('1')
                )
                signal = asyncio.run(self.strategy.generate_signal(negative_data))
                edge_cases_passed += 1
            except Exception:
                pass
            
            # 测试4: 数据不足
            total_edge_cases += 1
            try:
                # 清空历史数据
                self.strategy._price_history.clear()
                self.strategy._volume_history.clear()
                
                insufficient_data = HistoricalDataPoint(
                    timestamp=datetime.now(),
                    symbol="BTCUSDT",
                    close_price=Decimal('50000'),
                    volume=Decimal('1000')
                )
                signal = asyncio.run(self.strategy.generate_signal(insufficient_data))
                # 应该返回None
                if signal is None:
                    edge_cases_passed += 1
            except Exception:
                pass
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.test_results.append(TestResult(
                test_name="边界情况测试",
                passed=edge_cases_passed >= total_edge_cases * 0.5,  # 至少50%通过
                message=f"边界情况测试: {edge_cases_passed}/{total_edge_cases} 通过",
                execution_time=execution_time,
                details={
                    "passed_cases": edge_cases_passed,
                    "total_cases": total_edge_cases
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="边界情况测试",
                passed=False,
                message=f"边界情况测试失败: {str(e)}",
                execution_time=0
            ))
    
    def _test_performance(self):
        """测试性能。"""
        try:
            start_time = datetime.now()
            
            # 准备大量测试数据
            test_data = self._create_test_data(1000)
            execution_times = []
            
            # 测试信号生成性能
            for data_point in test_data:
                signal_start = datetime.now()
                asyncio.run(self.strategy.generate_signal(data_point))
                signal_time = (datetime.now() - signal_start).total_seconds()
                execution_times.append(signal_time)
            
            # 计算性能指标
            avg_time = statistics.mean(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)
            
            # 性能要求（可配置）
            max_acceptable_time = 0.1  # 100ms
            avg_acceptable_time = 0.05  # 50ms
            
            performance_ok = avg_time <= avg_acceptable_time and max_time <= max_acceptable_time
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            self.test_results.append(TestResult(
                test_name="性能测试",
                passed=performance_ok,
                message=f"平均执行时间: {avg_time:.4f}s, 最大: {max_time:.4f}s",
                execution_time=execution_time,
                details={
                    "avg_execution_time": avg_time,
                    "max_execution_time": max_time,
                    "min_execution_time": min_time,
                    "total_operations": len(execution_times),
                    "operations_per_second": len(execution_times) / execution_time if execution_time > 0 else 0
                }
            ))
            
        except Exception as e:
            self.test_results.append(TestResult(
                test_name="性能测试",
                passed=False,
                message=f"性能测试失败: {str(e)}",
                execution_time=0
            ))
    
    def _create_test_data(self, count: int) -> List[HistoricalDataPoint]:
        """创建测试数据。"""
        data_points = []
        base_price = 50000
        base_time = datetime.now() - timedelta(minutes=count)
        
        for i in range(count):
            # 模拟价格波动
            price_change = (i % 10 - 5) * 100  # -500 到 +400
            price = base_price + price_change + (i * 10)  # 总体上升趋势
            
            data_point = HistoricalDataPoint(
                timestamp=base_time + timedelta(minutes=i),
                symbol="BTCUSDT",
                close_price=Decimal(str(price)),
                volume=Decimal(str(1000 + i * 10))
            )
            data_points.append(data_point)
        
        return data_points
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告。"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.passed)
        failed_tests = total_tests - passed_tests
        
        total_execution_time = sum(result.execution_time for result in self.test_results)
        
        report = {
            "strategy_name": self.strategy.name,
            "strategy_version": self.strategy.version,
            "test_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "total_execution_time": total_execution_time
            },
            "test_results": [
                {
                    "test_name": result.test_name,
                    "passed": result.passed,
                    "message": result.message,
                    "execution_time": result.execution_time,
                    "details": result.details
                }
                for result in self.test_results
            ],
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议。"""
        recommendations = []
        
        # 检查失败的测试
        failed_tests = [result for result in self.test_results if not result.passed]
        
        if failed_tests:
            recommendations.append(f"有{len(failed_tests)}个测试失败，需要修复相关问题")
        
        # 检查性能
        performance_test = next((result for result in self.test_results if result.test_name == "性能测试"), None)
        if performance_test and performance_test.details:
            avg_time = performance_test.details.get('avg_execution_time', 0)
            if avg_time > 0.05:
                recommendations.append("策略执行时间较长，建议优化性能")
        
        # 检查信号生成率
        signal_test = next((result for result in self.test_results if result.test_name == "信号生成测试"), None)
        if signal_test and signal_test.details:
            signal_rate = signal_test.details.get('signal_rate', 0)
            if signal_rate < 0.01:
                recommendations.append("信号生成率较低，可能需要调整策略参数")
            elif signal_rate > 0.5:
                recommendations.append("信号生成率较高，建议增加过滤条件")
        
        if not recommendations:
            recommendations.append("策略测试通过，表现良好")
        
        return recommendations
    
    def save_report(self, filepath: str):
        """保存测试报告到文件。"""
        report = self._generate_test_report()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"测试报告已保存到: {filepath}")


class StrategyUnitTest(unittest.TestCase):
    """策略单元测试基类。"""
    
    def setUp(self):
        """测试设置。"""
        self.strategy = None  # 子类需要设置
        self.test_data = self._create_test_data(50)
    
    def _create_test_data(self, count: int) -> List[HistoricalDataPoint]:
        """创建测试数据。"""
        data_points = []
        base_price = 50000
        base_time = datetime.now() - timedelta(minutes=count)
        
        for i in range(count):
            price = base_price + (i % 10 - 5) * 100
            data_point = HistoricalDataPoint(
                timestamp=base_time + timedelta(minutes=i),
                symbol="BTCUSDT",
                close_price=Decimal(str(price)),
                volume=Decimal(str(1000 + i * 10))
            )
            data_points.append(data_point)
        
        return data_points
    
    def test_strategy_initialization(self):
        """测试策略初始化。"""
        self.assertIsNotNone(self.strategy)
        self.assertIsNotNone(self.strategy.name)
        self.assertIsNotNone(self.strategy.version)
        self.assertIsNotNone(self.strategy.config)
    
    def test_data_update(self):
        """测试数据更新。"""
        initial_count = len(self.strategy._price_history)
        
        for data_point in self.test_data:
            self.strategy.update_data(data_point)
        
        self.assertEqual(len(self.strategy._price_history), initial_count + len(self.test_data))
    
    def test_indicator_calculation(self):
        """测试指标计算。"""
        # 添加足够的数据
        for data_point in self.test_data:
            self.strategy.update_data(data_point)
        
        indicators = self.strategy.calculate_indicators(self.test_data[-1])
        self.assertIsInstance(indicators, TechnicalIndicators)
    
    async def test_signal_generation(self):
        """测试信号生成。"""
        for data_point in self.test_data:
            signal = await self.strategy.generate_signal(data_point)
            if signal:
                self.assertIsInstance(signal, StrategySignal)
                self.assertIn(signal.direction, ["UP", "DOWN"])
                self.assertIn(signal.confidence, ["LOW", "MEDIUM", "HIGH"])
                self.assertGreaterEqual(signal.probability, 0.5)
                self.assertLessEqual(signal.probability, 1.0)


def run_strategy_tests(strategy: BaseStrategy, save_report: bool = True, report_path: str = None) -> Dict[str, Any]:
    """运行策略测试的便捷函数。"""
    tester = StrategyTester(strategy)
    report = tester.run_all_tests()
    
    if save_report:
        if report_path is None:
            report_path = f"test_report_{strategy.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        tester.save_report(report_path)
    
    return report


if __name__ == "__main__":
    # 示例用法
    from backtesting.src.strategies.momentum_strategy import MomentumStrategy
    
    # 创建策略实例
    strategy = MomentumStrategy()
    
    # 运行测试
    report = run_strategy_tests(strategy)
    
    # 打印结果
    print(f"策略测试完成: {strategy.name}")
    print(f"测试通过率: {report['summary']['success_rate']:.2%}")
    print(f"总执行时间: {report['summary']['total_execution_time']:.4f}秒")
    
    for result in report['test_results']:
        status = "✓" if result['passed'] else "✗"
        print(f"{status} {result['test_name']}: {result['message']}")