"""Trading strategies module.

This module provides various trading strategies for the backtesting system.
All strategies inherit from BaseStrategy and implement the required interface."""

from .base_strategy import BaseStrategy, StrategySignal, TechnicalIndicators

# Import strategy implementations
from .momentum_strategy import MomentumStrategy, MomentumStrategyConfig
from .mean_reversion_strategy import MeanReversionStrategy, MeanReversionStrategyConfig
from .volatility_strategy import VolatilityStrategy, VolatilityStrategyConfig

__all__ = [
    'BaseStrategy',
    'StrategySignal', 
    'TechnicalIndicators',
    'MomentumStrategy',
    'MomentumStrategyConfig',
    'MeanReversionStrategy',
    'MeanReversionStrategyConfig',
    'VolatilityStrategy',
    'VolatilityStrategyConfig'
]