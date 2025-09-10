"""Performance analyzer for backtesting results.

This module provides comprehensive performance analysis tools for evaluating
backtesting results including risk metrics, return analysis, and comparison utilities.
"""

import math
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, validator

from ..models.backtest_result import BacktestResult
from ..models.backtest_trade import BacktestTrade


class PerformanceMetrics(BaseModel):
    """Comprehensive performance metrics."""
    # Basic metrics
    total_return: Decimal
    annualized_return: Decimal
    win_rate: float
    average_win: Decimal
    average_loss: Decimal
    profit_factor: float
    
    # Risk metrics
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: Decimal
    max_drawdown_duration_days: int
    value_at_risk_95: Decimal
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    largest_win: Decimal
    largest_loss: Decimal
    average_trade_duration_minutes: float
    
    # Time-based metrics
    trading_days: int
    trades_per_day: float
    
    # Advanced metrics
    calmar_ratio: float
    ulcer_index: float
    recovery_factor: float
    expectancy: Decimal

    class Config:
        json_encoders = {
            Decimal: str
        }


class DrawdownAnalysis(BaseModel):
    """Detailed drawdown analysis."""
    max_drawdown: Decimal
    max_drawdown_date: datetime
    max_drawdown_duration_days: int
    recovery_date: Optional[datetime]
    drawdown_periods: List[Dict[str, Any]]
    average_drawdown: Decimal
    drawdown_frequency: float

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class MonthlyReturns(BaseModel):
    """Monthly returns breakdown."""
    monthly_returns: Dict[str, float]  # "YYYY-MM": return_percentage
    best_month: Dict[str, Any]
    worst_month: Dict[str, Any]
    win_months: int
    total_months: int
    monthly_win_rate: float

    class Config:
        json_encoders = {
            Decimal: str
        }


class RiskAnalysis(BaseModel):
    """Risk analysis metrics."""
    volatility: float
    downside_volatility: float
    beta: Optional[float] = None  # If benchmark provided
    var_95: Decimal
    var_99: Decimal
    expected_shortfall_95: Decimal
    maximum_consecutive_losses: int
    maximum_consecutive_wins: int
    tail_ratio: float  # Right tail / left tail

    class Config:
        json_encoders = {
            Decimal: str
        }


class PerformanceAnalyzer:
    """Comprehensive performance analyzer for backtesting results."""

    def __init__(self, initial_capital: Decimal):
        self.initial_capital = initial_capital

    async def analyze_performance(self, backtest_result: BacktestResult, 
                                trades: List[BacktestTrade],
                                benchmark_returns: Optional[List[float]] = None) -> PerformanceMetrics:
        """Analyze overall performance of backtest results.
        
        Args:
            backtest_result: BacktestResult object
            trades: List of BacktestTrade objects
            benchmark_returns: Optional benchmark returns for comparison
            
        Returns:
            PerformanceMetrics with comprehensive analysis
        """
        if not trades:
            return await self._create_empty_metrics(backtest_result)

        # Calculate basic metrics
        total_return = backtest_result.total_profit_loss
        period_days = (backtest_result.end_date - backtest_result.start_date).days
        annualized_return = await self._calculate_annualized_return(total_return, period_days)
        
        # Trade statistics
        winning_trades = [t for t in trades if t.was_successful]
        losing_trades = [t for t in trades if not t.was_successful]
        
        win_rate = len(winning_trades) / len(trades) if trades else 0
        average_win = (
            sum(t.profit_loss for t in winning_trades) / len(winning_trades)
            if winning_trades else Decimal('0')
        )
        average_loss = (
            sum(abs(t.profit_loss) for t in losing_trades) / len(losing_trades)
            if losing_trades else Decimal('0')
        )
        
        profit_factor = (
            float(average_win) / float(average_loss) 
            if average_loss > 0 else 0
        )
        
        # Risk metrics
        returns_series = await self._create_returns_series(trades)
        sharpe_ratio = await self._calculate_sharpe_ratio(returns_series)
        sortino_ratio = await self._calculate_sortino_ratio(returns_series)
        
        # Drawdown analysis
        drawdown_analysis = await self.analyze_drawdowns(trades)
        max_drawdown = drawdown_analysis.max_drawdown
        max_drawdown_duration = drawdown_analysis.max_drawdown_duration_days
        
        # Value at Risk
        var_95 = await self._calculate_var(returns_series, 0.05)
        
        # Trade details
        largest_win = max((t.profit_loss for t in trades), default=Decimal('0'))
        largest_loss = min((t.profit_loss for t in trades), default=Decimal('0'))
        
        avg_duration = (
            sum(t.contract_duration_minutes for t in trades) / len(trades)
            if trades else 0
        )
        
        # Advanced metrics
        calmar_ratio = await self._calculate_calmar_ratio(annualized_return, max_drawdown)
        ulcer_index = await self._calculate_ulcer_index(returns_series)
        recovery_factor = await self._calculate_recovery_factor(total_return, max_drawdown)
        
        # Expectancy calculation
        expectancy = await self._calculate_expectancy(winning_trades, losing_trades)

        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            win_rate=win_rate,
            average_win=average_win,
            average_loss=average_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration_days=max_drawdown_duration,
            value_at_risk_95=var_95,
            total_trades=len(trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            largest_win=largest_win,
            largest_loss=largest_loss,
            average_trade_duration_minutes=avg_duration,
            trading_days=period_days,
            trades_per_day=len(trades) / period_days if period_days > 0 else 0,
            calmar_ratio=calmar_ratio,
            ulcer_index=ulcer_index,
            recovery_factor=recovery_factor,
            expectancy=expectancy
        )

    async def analyze_drawdowns(self, trades: List[BacktestTrade]) -> DrawdownAnalysis:
        """Analyze drawdown characteristics.
        
        Args:
            trades: List of BacktestTrade objects
            
        Returns:
            DrawdownAnalysis with detailed drawdown information
        """
        if not trades:
            return DrawdownAnalysis(
                max_drawdown=Decimal('0'),
                max_drawdown_date=datetime.utcnow(),
                max_drawdown_duration_days=0,
                recovery_date=None,
                drawdown_periods=[],
                average_drawdown=Decimal('0'),
                drawdown_frequency=0.0
            )

        # Calculate running balance and drawdowns
        running_balance = self.initial_capital
        peak_balance = running_balance
        drawdowns = []
        drawdown_periods = []
        current_drawdown_start = None
        max_drawdown = Decimal('0')
        max_drawdown_date = trades[0].created_at
        max_drawdown_duration = 0
        
        for i, trade in enumerate(trades):
            running_balance += trade.profit_loss
            
            if running_balance > peak_balance:
                # New peak - end current drawdown period if any
                if current_drawdown_start is not None:
                    duration_days = (trade.created_at - current_drawdown_start).days
                    drawdown_periods.append({
                        "start_date": current_drawdown_start,
                        "end_date": trade.created_at,
                        "duration_days": duration_days,
                        "max_drawdown": max((d for d in drawdowns[len(drawdown_periods)*-1:]), default=0)
                    })
                    current_drawdown_start = None
                
                peak_balance = running_balance
            else:
                # In drawdown
                if current_drawdown_start is None:
                    current_drawdown_start = trade.created_at
                
                current_drawdown = peak_balance - running_balance
                drawdowns.append(current_drawdown)
                
                if current_drawdown > max_drawdown:
                    max_drawdown = current_drawdown
                    max_drawdown_date = trade.created_at
        
        # Handle ongoing drawdown at the end
        if current_drawdown_start is not None:
            duration_days = (trades[-1].created_at - current_drawdown_start).days
            drawdown_periods.append({
                "start_date": current_drawdown_start,
                "end_date": trades[-1].created_at,
                "duration_days": duration_days,
                "max_drawdown": max_drawdown,
                "recovery_date": None  # Still in drawdown
            })
            max_drawdown_duration = duration_days
        else:
            # Find maximum drawdown duration
            max_drawdown_duration = max((p["duration_days"] for p in drawdown_periods), default=0)
        
        average_drawdown = (
            sum(drawdowns) / len(drawdowns) if drawdowns else Decimal('0')
        )
        
        drawdown_frequency = len(drawdown_periods) / len(trades) if trades else 0.0

        return DrawdownAnalysis(
            max_drawdown=max_drawdown,
            max_drawdown_date=max_drawdown_date,
            max_drawdown_duration_days=max_drawdown_duration,
            recovery_date=None,  # Would need additional logic to determine
            drawdown_periods=drawdown_periods,
            average_drawdown=average_drawdown,
            drawdown_frequency=drawdown_frequency
        )

    async def analyze_monthly_returns(self, trades: List[BacktestTrade]) -> MonthlyReturns:
        """Analyze monthly returns breakdown.
        
        Args:
            trades: List of BacktestTrade objects
            
        Returns:
            MonthlyReturns with monthly performance data
        """
        if not trades:
            return MonthlyReturns(
                monthly_returns={},
                best_month={"month": "", "return": 0.0},
                worst_month={"month": "", "return": 0.0},
                win_months=0,
                total_months=0,
                monthly_win_rate=0.0
            )

        # Group trades by month
        monthly_trades = {}
        for trade in trades:
            month_key = trade.created_at.strftime("%Y-%m")
            if month_key not in monthly_trades:
                monthly_trades[month_key] = []
            monthly_trades[month_key].append(trade)

        # Calculate monthly returns
        monthly_returns = {}
        for month, month_trades in monthly_trades.items():
            month_pnl = sum(trade.profit_loss for trade in month_trades)
            # Calculate return as percentage of allocated capital for that month
            allocated_capital = len(month_trades) * month_trades[0].bet_amount
            return_pct = float(month_pnl / allocated_capital) * 100 if allocated_capital > 0 else 0
            monthly_returns[month] = return_pct

        # Find best and worst months
        if monthly_returns:
            best_month_key = max(monthly_returns, key=monthly_returns.get)
            worst_month_key = min(monthly_returns, key=monthly_returns.get)
            
            best_month = {"month": best_month_key, "return": monthly_returns[best_month_key]}
            worst_month = {"month": worst_month_key, "return": monthly_returns[worst_month_key]}
        else:
            best_month = {"month": "", "return": 0.0}
            worst_month = {"month": "", "return": 0.0}

        # Count winning months
        win_months = sum(1 for ret in monthly_returns.values() if ret > 0)
        total_months = len(monthly_returns)
        monthly_win_rate = win_months / total_months if total_months > 0 else 0.0

        return MonthlyReturns(
            monthly_returns=monthly_returns,
            best_month=best_month,
            worst_month=worst_month,
            win_months=win_months,
            total_months=total_months,
            monthly_win_rate=monthly_win_rate
        )

    async def analyze_risk(self, trades: List[BacktestTrade],
                          benchmark_returns: Optional[List[float]] = None) -> RiskAnalysis:
        """Analyze risk characteristics.
        
        Args:
            trades: List of BacktestTrade objects
            benchmark_returns: Optional benchmark returns for beta calculation
            
        Returns:
            RiskAnalysis with risk metrics
        """
        if not trades:
            return RiskAnalysis(
                volatility=0.0,
                downside_volatility=0.0,
                var_95=Decimal('0'),
                var_99=Decimal('0'),
                expected_shortfall_95=Decimal('0'),
                maximum_consecutive_losses=0,
                maximum_consecutive_wins=0,
                tail_ratio=1.0
            )

        # Create returns series
        returns = [float(trade.profit_loss / trade.bet_amount) for trade in trades]
        
        # Calculate volatility
        volatility = float(np.std(returns)) if len(returns) > 1 else 0.0
        
        # Downside volatility (only negative returns)
        negative_returns = [r for r in returns if r < 0]
        downside_volatility = float(np.std(negative_returns)) if len(negative_returns) > 1 else 0.0
        
        # Value at Risk calculations
        var_95 = await self._calculate_var(returns, 0.05)
        var_99 = await self._calculate_var(returns, 0.01)
        
        # Expected Shortfall (Conditional VaR)
        expected_shortfall_95 = await self._calculate_expected_shortfall(returns, 0.05)
        
        # Consecutive wins/losses
        consecutive_stats = await self._calculate_consecutive_stats(trades)
        
        # Tail ratio
        tail_ratio = await self._calculate_tail_ratio(returns)
        
        # Beta calculation if benchmark provided
        beta = None
        if benchmark_returns and len(benchmark_returns) == len(returns):
            beta = await self._calculate_beta(returns, benchmark_returns)

        return RiskAnalysis(
            volatility=volatility,
            downside_volatility=downside_volatility,
            beta=beta,
            var_95=var_95,
            var_99=var_99,
            expected_shortfall_95=expected_shortfall_95,
            maximum_consecutive_losses=consecutive_stats["max_losses"],
            maximum_consecutive_wins=consecutive_stats["max_wins"],
            tail_ratio=tail_ratio
        )

    async def compare_strategies(self, results: List[Tuple[BacktestResult, List[BacktestTrade]]]) -> Dict[str, Any]:
        """Compare multiple strategy results.
        
        Args:
            results: List of (BacktestResult, List[BacktestTrade]) tuples
            
        Returns:
            Dictionary with comparison metrics
        """
        if not results:
            return {"error": "No results to compare"}

        comparison = {}
        
        for backtest_result, trades in results:
            strategy_name = backtest_result.strategy_name
            
            # Analyze performance for each strategy
            metrics = await self.analyze_performance(backtest_result, trades)
            
            comparison[strategy_name] = {
                "total_return": float(metrics.total_return),
                "annualized_return": float(metrics.annualized_return),
                "win_rate": metrics.win_rate,
                "sharpe_ratio": metrics.sharpe_ratio,
                "max_drawdown": float(metrics.max_drawdown),
                "total_trades": metrics.total_trades,
                "profit_factor": metrics.profit_factor,
                "calmar_ratio": metrics.calmar_ratio
            }

        # Find best strategy for each metric
        best_by_metric = {}
        metrics_to_compare = ["total_return", "annualized_return", "win_rate", "sharpe_ratio", "profit_factor", "calmar_ratio"]
        
        for metric in metrics_to_compare:
            best_strategy = max(comparison.keys(), 
                              key=lambda x: comparison[x][metric])
            best_by_metric[f"best_{metric}"] = {
                "strategy": best_strategy,
                "value": comparison[best_strategy][metric]
            }

        return {
            "individual_results": comparison,
            "best_by_metric": best_by_metric,
            "summary": {
                "strategies_compared": len(results),
                "overall_best": best_by_metric.get("best_sharpe_ratio", {}).get("strategy", "Unknown")
            }
        }

    # Helper methods
    async def _create_empty_metrics(self, backtest_result: BacktestResult) -> PerformanceMetrics:
        """Create empty metrics for cases with no trades."""
        return PerformanceMetrics(
            total_return=Decimal('0'),
            annualized_return=Decimal('0'),
            win_rate=0.0,
            average_win=Decimal('0'),
            average_loss=Decimal('0'),
            profit_factor=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown=Decimal('0'),
            max_drawdown_duration_days=0,
            value_at_risk_95=Decimal('0'),
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            largest_win=Decimal('0'),
            largest_loss=Decimal('0'),
            average_trade_duration_minutes=0.0,
            trading_days=(backtest_result.end_date - backtest_result.start_date).days,
            trades_per_day=0.0,
            calmar_ratio=0.0,
            ulcer_index=0.0,
            recovery_factor=0.0,
            expectancy=Decimal('0')
        )

    async def _calculate_annualized_return(self, total_return: Decimal, period_days: int) -> Decimal:
        """Calculate annualized return."""
        if period_days <= 0:
            return Decimal('0')
        
        years = period_days / 365.25
        if years <= 0:
            return total_return
        
        return_rate = float(total_return / self.initial_capital)
        annualized = ((1 + return_rate) ** (1 / years)) - 1
        
        return Decimal(str(round(annualized * 100, 4)))  # Return as percentage

    async def _create_returns_series(self, trades: List[BacktestTrade]) -> List[float]:
        """Create returns series from trades."""
        return [float(trade.profit_loss / trade.bet_amount) for trade in trades]

    async def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) < 2:
            return 0.0
        
        excess_returns = [r - risk_free_rate for r in returns]
        mean_excess = sum(excess_returns) / len(excess_returns)
        
        if len(excess_returns) == 1:
            return 0.0
        
        std_dev = float(np.std(excess_returns, ddof=1))
        
        return mean_excess / std_dev if std_dev > 0 else 0.0

    async def _calculate_sortino_ratio(self, returns: List[float], risk_free_rate: float = 0.0) -> float:
        """Calculate Sortino ratio."""
        if len(returns) < 2:
            return 0.0
        
        excess_returns = [r - risk_free_rate for r in returns]
        mean_excess = sum(excess_returns) / len(excess_returns)
        
        # Calculate downside deviation
        negative_returns = [r for r in excess_returns if r < 0]
        if len(negative_returns) < 2:
            return float('inf') if mean_excess > 0 else 0.0
        
        downside_std = float(np.std(negative_returns, ddof=1))
        
        return mean_excess / downside_std if downside_std > 0 else 0.0

    async def _calculate_var(self, returns: List[float], alpha: float) -> Decimal:
        """Calculate Value at Risk."""
        if not returns:
            return Decimal('0')
        
        sorted_returns = sorted(returns)
        index = int(alpha * len(sorted_returns))
        
        if index >= len(sorted_returns):
            return Decimal(str(sorted_returns[-1]))
        
        return Decimal(str(abs(sorted_returns[index])))

    async def _calculate_expected_shortfall(self, returns: List[float], alpha: float) -> Decimal:
        """Calculate Expected Shortfall (Conditional VaR)."""
        if not returns:
            return Decimal('0')
        
        var_threshold = await self._calculate_var(returns, alpha)
        
        tail_losses = [abs(r) for r in returns if r <= -float(var_threshold)]
        
        if not tail_losses:
            return var_threshold
        
        return Decimal(str(sum(tail_losses) / len(tail_losses)))

    async def _calculate_calmar_ratio(self, annualized_return: Decimal, max_drawdown: Decimal) -> float:
        """Calculate Calmar ratio."""
        if max_drawdown <= 0:
            return float('inf') if annualized_return > 0 else 0.0
        
        return float(annualized_return / max_drawdown)

    async def _calculate_ulcer_index(self, returns: List[float]) -> float:
        """Calculate Ulcer Index."""
        if len(returns) < 2:
            return 0.0
        
        # Calculate running maximum and drawdowns
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - running_max) / running_max * 100
        
        # Ulcer Index is RMS of drawdowns
        squared_drawdowns = drawdowns ** 2
        mean_squared = np.mean(squared_drawdowns)
        
        return float(np.sqrt(mean_squared))

    async def _calculate_recovery_factor(self, total_return: Decimal, max_drawdown: Decimal) -> float:
        """Calculate Recovery Factor."""
        if max_drawdown <= 0:
            return float('inf') if total_return > 0 else 0.0
        
        return float(total_return / max_drawdown)

    async def _calculate_expectancy(self, winning_trades: List[BacktestTrade], 
                                  losing_trades: List[BacktestTrade]) -> Decimal:
        """Calculate expectancy per trade."""
        total_trades = len(winning_trades) + len(losing_trades)
        if total_trades == 0:
            return Decimal('0')
        
        win_rate = len(winning_trades) / total_trades
        loss_rate = len(losing_trades) / total_trades
        
        avg_win = (
            sum(t.profit_loss for t in winning_trades) / len(winning_trades)
            if winning_trades else Decimal('0')
        )
        avg_loss = (
            sum(abs(t.profit_loss) for t in losing_trades) / len(losing_trades)
            if losing_trades else Decimal('0')
        )
        
        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
        
        return expectancy

    async def _calculate_consecutive_stats(self, trades: List[BacktestTrade]) -> Dict[str, int]:
        """Calculate maximum consecutive wins and losses."""
        if not trades:
            return {"max_wins": 0, "max_losses": 0}
        
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in trades:
            if trade.was_successful:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
        
        return {"max_wins": max_wins, "max_losses": max_losses}

    async def _calculate_tail_ratio(self, returns: List[float]) -> float:
        """Calculate tail ratio (right tail / left tail)."""
        if len(returns) < 10:
            return 1.0
        
        # Use 95th percentile for tails
        sorted_returns = sorted(returns)
        
        # Right tail (95th percentile)
        right_tail_index = int(0.95 * len(sorted_returns))
        right_tail = abs(sorted_returns[right_tail_index])
        
        # Left tail (5th percentile)
        left_tail_index = int(0.05 * len(sorted_returns))
        left_tail = abs(sorted_returns[left_tail_index])
        
        return right_tail / left_tail if left_tail > 0 else 1.0

    async def _calculate_beta(self, returns: List[float], benchmark_returns: List[float]) -> float:
        """Calculate beta relative to benchmark."""
        if len(returns) != len(benchmark_returns) or len(returns) < 2:
            return None
        
        # Calculate covariance and variance
        mean_returns = sum(returns) / len(returns)
        mean_benchmark = sum(benchmark_returns) / len(benchmark_returns)
        
        covariance = sum(
            (r - mean_returns) * (b - mean_benchmark) 
            for r, b in zip(returns, benchmark_returns)
        ) / (len(returns) - 1)
        
        benchmark_variance = sum(
            (b - mean_benchmark) ** 2 for b in benchmark_returns
        ) / (len(benchmark_returns) - 1)
        
        return covariance / benchmark_variance if benchmark_variance > 0 else 0.0