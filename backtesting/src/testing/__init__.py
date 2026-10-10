#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略测试模块

提供策略验证、单元测试、性能测试等功能。
"""

from .strategy_tester import (
    StrategyTester,
    StrategyUnitTest,
    TestResult,
    PerformanceMetrics,
    run_strategy_tests
)

__all__ = [
    'StrategyTester',
    'StrategyUnitTest', 
    'TestResult',
    'PerformanceMetrics',
    'run_strategy_tests'
]

__version__ = '1.0.0'