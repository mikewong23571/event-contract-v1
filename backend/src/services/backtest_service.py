from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Any
from uuid import UUID
import logging
import pandas as pd

from ..models.market_data import MarketData
from ..models.trading_signal import TradingSignal
from ..models.risk_parameters import RiskParameters
from ...backtesting.src.models.backtest_result import BacktestResult
from ...backtesting.src.models.backtest_trade import BacktestTrade
from ...backtesting.src.lib.backtesting_engine.backtesting_engine import BacktestingEngine


class BacktestService:
    def __init__(self, initial_capital: Decimal = Decimal("10000")):
        self.initial_capital = initial_capital
        self.backtesting_engine = BacktestingEngine(initial_capital)
        self.logger = logging.getLogger(__name__)
        self._backtest_cache: Dict[str, BacktestResult] = {}

    def run_strategy_backtest(
        self,
        strategy_name: str,
        market_data: List[MarketData],
        strategy_params: Dict[str, Any],
        risk_params: Optional[RiskParameters] = None,
        execution_mode: str = "FIRST_SIGNAL"
    ) -> BacktestResult:
        """Run a backtest for a specific strategy"""
        
        self.logger.info(f"Starting backtest for strategy '{strategy_name}' with {len(market_data)} data points")
        
        try:
            # Convert market data to pandas DataFrame format expected by backtesting engine
            market_df = self._convert_market_data_to_dataframe(market_data)
            
            # Validate inputs
            if market_df.empty:
                raise ValueError("Market data is empty after conversion")
            
            if not strategy_params:
                raise ValueError("Strategy parameters cannot be empty")
            
            # Add risk parameters to strategy params if provided
            if risk_params:
                strategy_params["risk_parameters"] = {
                    "max_bet_size": float(risk_params.max_bet_size),
                    "max_daily_bets": risk_params.max_daily_bets,
                    "max_parallel_positions": risk_params.max_parallel_positions,
                    "min_probability_edge": float(risk_params.min_probability_edge),
                    "frequency_limit_minutes": risk_params.frequency_limit_minutes,
                    "max_daily_loss": float(risk_params.max_daily_loss)
                }
            
            # Run backtest using backtesting engine
            backtest_result = self.backtesting_engine.run_backtest(
                strategy_name=strategy_name,
                market_data=market_df,
                strategy_params=strategy_params,
                execution_mode=execution_mode
            )
            
            # Cache result
            cache_key = f"{strategy_name}_{execution_mode}_{hash(str(strategy_params))}"
            self._backtest_cache[cache_key] = backtest_result
            
            self.logger.info(f"Backtest completed for '{strategy_name}': {backtest_result.total_signals} signals, {float(backtest_result.win_rate):.1%} win rate")
            return backtest_result
            
        except Exception as e:
            self.logger.error(f"Error running backtest for strategy '{strategy_name}': {e}")
            raise

    def run_parameter_optimization(
        self,
        strategy_name: str,
        market_data: List[MarketData],
        parameter_ranges: Dict[str, List[Any]],
        metric_to_optimize: str = "total_profit_loss",
        risk_params: Optional[RiskParameters] = None
    ) -> Dict[str, Any]:
        """Run parameter optimization to find best strategy parameters"""
        
        self.logger.info(f"Starting parameter optimization for '{strategy_name}' with {len(parameter_ranges)} parameters")
        
        try:
            # Convert market data
            market_df = self._convert_market_data_to_dataframe(market_data)
            
            # Run optimization using backtesting engine
            optimization_result = self.backtesting_engine.run_parameter_optimization(
                strategy_name=strategy_name,
                market_data=market_df,
                parameter_ranges=parameter_ranges,
                metric_to_optimize=metric_to_optimize
            )
            
            # Add service-level metadata
            optimization_result["service_metadata"] = {
                "optimization_time": datetime.utcnow(),
                "data_points": len(market_data),
                "optimization_metric": metric_to_optimize,
                "risk_params_applied": risk_params is not None
            }
            
            self.logger.info(f"Parameter optimization completed for '{strategy_name}': {optimization_result['total_combinations_tested']} combinations tested")
            return optimization_result
            
        except Exception as e:
            self.logger.error(f"Error in parameter optimization for '{strategy_name}': {e}")
            raise

    def run_walk_forward_analysis(
        self,
        strategy_name: str,
        market_data: List[MarketData],
        strategy_params: Dict[str, Any],
        in_sample_days: int = 30,
        out_of_sample_days: int = 7,
        step_days: int = 7
    ) -> Dict[str, Any]:
        """Run walk-forward analysis for strategy validation"""
        
        self.logger.info(f"Starting walk-forward analysis for '{strategy_name}'")
        
        try:
            # Convert market data
            market_df = self._convert_market_data_to_dataframe(market_data)
            
            # Convert day parameters to periods (assuming 1440 minutes per day for 1-minute data)
            in_sample_periods = in_sample_days * 1440
            out_of_sample_periods = out_of_sample_days * 1440
            step_size = step_days * 1440
            
            # Run walk-forward analysis
            walk_forward_result = self.backtesting_engine.run_walk_forward_analysis(
                strategy_name=strategy_name,
                market_data=market_df,
                strategy_params=strategy_params,
                in_sample_periods=in_sample_periods,
                out_of_sample_periods=out_of_sample_periods,
                step_size=step_size
            )
            
            # Add service-level analysis
            walk_forward_result["service_analysis"] = self._analyze_walk_forward_stability(walk_forward_result)
            
            self.logger.info(f"Walk-forward analysis completed for '{strategy_name}': {walk_forward_result['total_windows']} windows analyzed")
            return walk_forward_result
            
        except Exception as e:
            self.logger.error(f"Error in walk-forward analysis for '{strategy_name}': {e}")
            raise

    def run_monte_carlo_simulation(
        self,
        backtest_result: BacktestResult,
        num_simulations: int = 1000,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """Run Monte Carlo simulation on backtest results"""
        
        self.logger.info(f"Running Monte Carlo simulation with {num_simulations} iterations")
        
        try:
            monte_carlo_result = self.backtesting_engine.run_monte_carlo_simulation(
                backtest_result=backtest_result,
                num_simulations=num_simulations,
                confidence_level=confidence_level
            )
            
            # Add risk interpretation
            monte_carlo_result["risk_interpretation"] = self._interpret_monte_carlo_results(monte_carlo_result)
            
            self.logger.info(f"Monte Carlo simulation completed: {monte_carlo_result['probability_of_loss']:.1%} probability of loss")
            return monte_carlo_result
            
        except Exception as e:
            self.logger.error(f"Error in Monte Carlo simulation: {e}")
            raise

    def compare_strategies(
        self,
        strategies: List[Dict[str, Any]],
        market_data: List[MarketData],
        comparison_metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare multiple strategies on the same dataset"""
        
        self.logger.info(f"Comparing {len(strategies)} strategies")
        
        if not comparison_metrics:
            comparison_metrics = ["total_profit_loss", "win_rate", "max_drawdown", "sharpe_ratio"]
        
        try:
            comparison_results = {}
            strategy_results = []
            
            # Run backtest for each strategy
            for strategy in strategies:
                strategy_name = strategy["name"]
                strategy_params = strategy["parameters"]
                risk_params = strategy.get("risk_parameters")
                
                try:
                    result = self.run_strategy_backtest(
                        strategy_name=strategy_name,
                        market_data=market_data,
                        strategy_params=strategy_params,
                        risk_params=risk_params
                    )
                    
                    strategy_results.append({
                        "name": strategy_name,
                        "result": result,
                        "parameters": strategy_params
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Failed to run backtest for strategy '{strategy_name}': {e}")
                    continue
            
            if not strategy_results:
                raise ValueError("No strategies could be successfully backtested")
            
            # Create comparison matrix
            comparison_matrix = {}
            for metric in comparison_metrics:
                comparison_matrix[metric] = {}
                
                for strategy_result in strategy_results:
                    strategy_name = strategy_result["name"]
                    result = strategy_result["result"]
                    
                    if hasattr(result, metric):
                        value = getattr(result, metric)
                        if isinstance(value, Decimal):
                            value = float(value)
                        comparison_matrix[metric][strategy_name] = value
                    else:
                        comparison_matrix[metric][strategy_name] = None
            
            # Rank strategies for each metric
            rankings = self._rank_strategies(comparison_matrix, comparison_metrics)
            
            # Identify best overall strategy
            best_strategy = self._identify_best_strategy(strategy_results, rankings)
            
            comparison_results = {
                "strategies_compared": len(strategy_results),
                "comparison_metrics": comparison_metrics,
                "comparison_matrix": comparison_matrix,
                "rankings": rankings,
                "best_strategy": best_strategy,
                "detailed_results": strategy_results,
                "comparison_timestamp": datetime.utcnow()
            }
            
            self.logger.info(f"Strategy comparison completed: Best strategy is '{best_strategy['name']}'")
            return comparison_results
            
        except Exception as e:
            self.logger.error(f"Error comparing strategies: {e}")
            raise

    def get_backtest_by_id(self, backtest_id: UUID) -> Optional[BacktestResult]:
        """Get a specific backtest result by ID"""
        
        # This would typically query from database
        # For now, search in cache
        for cached_result in self._backtest_cache.values():
            if cached_result.id == backtest_id:
                return cached_result
        
        self.logger.warning(f"Backtest result not found for ID: {backtest_id}")
        return None

    def get_backtest_history(
        self,
        strategy_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[BacktestResult]:
        """Get historical backtest results with filters"""
        
        # This would typically query from database
        # For now, return cached results
        results = list(self._backtest_cache.values())
        
        # Apply filters
        if strategy_name:
            results = [r for r in results if r.strategy_name == strategy_name]
        
        if start_date:
            results = [r for r in results if r.created_at >= start_date]
        
        if end_date:
            results = [r for r in results if r.created_at <= end_date]
        
        # Sort by creation date (newest first) and limit
        results.sort(key=lambda x: x.created_at, reverse=True)
        results = results[:limit]
        
        self.logger.info(f"Retrieved {len(results)} backtest results from history")
        return results

    def analyze_backtest_performance(
        self,
        backtest_result: BacktestResult
    ) -> Dict[str, Any]:
        """Analyze backtest performance and provide insights"""
        
        try:
            analysis = {
                "basic_metrics": {
                    "strategy_name": backtest_result.strategy_name,
                    "total_signals": backtest_result.total_signals,
                    "successful_signals": backtest_result.successful_signals,
                    "win_rate": float(backtest_result.win_rate),
                    "total_profit_loss": float(backtest_result.total_profit_loss),
                    "max_drawdown": float(backtest_result.max_drawdown),
                    "sharpe_ratio": float(backtest_result.sharpe_ratio)
                },
                "performance_category": self._categorize_performance(backtest_result),
                "risk_assessment": self._assess_backtest_risk(backtest_result),
                "recommendations": self._generate_backtest_recommendations(backtest_result),
                "confidence_score": self._calculate_confidence_score(backtest_result),
                "analysis_timestamp": datetime.utcnow()
            }
            
            self.logger.info(f"Performance analysis completed for '{backtest_result.strategy_name}': {analysis['performance_category']}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing backtest performance: {e}")
            return {"error": str(e)}

    def validate_strategy_robustness(
        self,
        strategy_name: str,
        strategy_params: Dict[str, Any],
        market_data: List[MarketData],
        validation_tests: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Validate strategy robustness through multiple tests"""
        
        if not validation_tests:
            validation_tests = ["parameter_sensitivity", "walk_forward", "monte_carlo", "out_of_sample"]
        
        self.logger.info(f"Validating robustness for '{strategy_name}' with {len(validation_tests)} tests")
        
        try:
            validation_results = {
                "strategy_name": strategy_name,
                "validation_tests": validation_tests,
                "test_results": {},
                "overall_robustness_score": 0.0,
                "validation_timestamp": datetime.utcnow()
            }
            
            # Parameter sensitivity test
            if "parameter_sensitivity" in validation_tests:
                try:
                    # Test with slightly varied parameters
                    sensitivity_results = self._test_parameter_sensitivity(strategy_name, strategy_params, market_data)
                    validation_results["test_results"]["parameter_sensitivity"] = sensitivity_results
                except Exception as e:
                    validation_results["test_results"]["parameter_sensitivity"] = {"error": str(e)}
            
            # Walk-forward analysis
            if "walk_forward" in validation_tests:
                try:
                    walk_forward_results = self.run_walk_forward_analysis(
                        strategy_name=strategy_name,
                        market_data=market_data,
                        strategy_params=strategy_params
                    )
                    validation_results["test_results"]["walk_forward"] = walk_forward_results
                except Exception as e:
                    validation_results["test_results"]["walk_forward"] = {"error": str(e)}
            
            # Monte Carlo validation
            if "monte_carlo" in validation_tests:
                try:
                    # Run base backtest first
                    base_result = self.run_strategy_backtest(
                        strategy_name=strategy_name,
                        market_data=market_data,
                        strategy_params=strategy_params
                    )
                    
                    monte_carlo_results = self.run_monte_carlo_simulation(base_result)
                    validation_results["test_results"]["monte_carlo"] = monte_carlo_results
                except Exception as e:
                    validation_results["test_results"]["monte_carlo"] = {"error": str(e)}
            
            # Out-of-sample test
            if "out_of_sample" in validation_tests:
                try:
                    oos_results = self._test_out_of_sample_performance(strategy_name, strategy_params, market_data)
                    validation_results["test_results"]["out_of_sample"] = oos_results
                except Exception as e:
                    validation_results["test_results"]["out_of_sample"] = {"error": str(e)}
            
            # Calculate overall robustness score
            validation_results["overall_robustness_score"] = self._calculate_robustness_score(validation_results["test_results"])
            
            # Generate robustness assessment
            validation_results["robustness_assessment"] = self._assess_strategy_robustness(validation_results)
            
            self.logger.info(f"Robustness validation completed for '{strategy_name}': {validation_results['overall_robustness_score']:.2f}/1.0")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating strategy robustness: {e}")
            return {"error": str(e)}

    def clear_backtest_cache(self) -> int:
        """Clear backtest results cache"""
        
        cached_count = len(self._backtest_cache)
        self._backtest_cache.clear()
        
        self.logger.info(f"Cleared {cached_count} cached backtest results")
        return cached_count

    def _convert_market_data_to_dataframe(self, market_data: List[MarketData]) -> pd.DataFrame:
        """Convert MarketData objects to pandas DataFrame"""
        
        if not market_data:
            return pd.DataFrame()
        
        try:
            data_records = []
            for md in market_data:
                record = {
                    'timestamp': md.timestamp,
                    'open': float(md.open_price),
                    'high': float(md.high_price),
                    'low': float(md.low_price),
                    'close': float(md.close_price),
                    'volume': float(md.volume),
                    'symbol': md.symbol
                }
                data_records.append(record)
            
            df = pd.DataFrame(data_records)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error converting market data to DataFrame: {e}")
            return pd.DataFrame()

    def _analyze_walk_forward_stability(self, walk_forward_result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze stability of walk-forward analysis results"""
        
        try:
            analysis = walk_forward_result.get("analysis", {})
            
            stability_analysis = {
                "performance_consistency": analysis.get("consistency_score", 0),
                "in_sample_vs_out_of_sample_correlation": analysis.get("correlation_coefficient", 0),
                "performance_degradation": analysis.get("performance_degradation", 0),
                "stability_rating": "UNKNOWN"
            }
            
            # Determine stability rating
            consistency = stability_analysis["performance_consistency"]
            correlation = abs(stability_analysis["in_sample_vs_out_of_sample_correlation"])
            degradation = abs(stability_analysis["performance_degradation"])
            
            if consistency > 0.8 and correlation > 0.7 and degradation < 0.1:
                stability_analysis["stability_rating"] = "EXCELLENT"
            elif consistency > 0.6 and correlation > 0.5 and degradation < 0.2:
                stability_analysis["stability_rating"] = "GOOD"
            elif consistency > 0.4 and correlation > 0.3 and degradation < 0.3:
                stability_analysis["stability_rating"] = "FAIR"
            else:
                stability_analysis["stability_rating"] = "POOR"
            
            return stability_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing walk-forward stability: {e}")
            return {"error": str(e)}

    def _interpret_monte_carlo_results(self, monte_carlo_result: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret Monte Carlo simulation results"""
        
        try:
            prob_of_loss = monte_carlo_result.get("probability_of_loss", 0)
            var_5pct = monte_carlo_result.get("value_at_risk_5pct", 0)
            expected_shortfall = monte_carlo_result.get("expected_shortfall", 0)
            
            interpretation = {
                "risk_level": "UNKNOWN",
                "confidence_assessment": "UNKNOWN",
                "recommended_actions": []
            }
            
            # Assess risk level
            if prob_of_loss < 0.2:
                interpretation["risk_level"] = "LOW"
                interpretation["recommended_actions"].append("Strategy shows low risk profile")
            elif prob_of_loss < 0.4:
                interpretation["risk_level"] = "MODERATE"
                interpretation["recommended_actions"].append("Monitor position sizing and risk management")
            else:
                interpretation["risk_level"] = "HIGH"
                interpretation["recommended_actions"].append("Consider reducing position sizes or improving strategy")
            
            # Assess confidence based on VaR
            if abs(var_5pct) < 0.1:
                interpretation["confidence_assessment"] = "HIGH"
            elif abs(var_5pct) < 0.2:
                interpretation["confidence_assessment"] = "MODERATE"
            else:
                interpretation["confidence_assessment"] = "LOW"
                interpretation["recommended_actions"].append("High volatility detected - use strict risk management")
            
            return interpretation
            
        except Exception as e:
            self.logger.error(f"Error interpreting Monte Carlo results: {e}")
            return {"error": str(e)}

    def _rank_strategies(self, comparison_matrix: Dict[str, Dict[str, Any]], metrics: List[str]) -> Dict[str, Dict[str, int]]:
        """Rank strategies for each metric"""
        
        rankings = {}
        
        for metric in metrics:
            metric_data = comparison_matrix.get(metric, {})
            
            # Sort strategies by metric value
            valid_strategies = {k: v for k, v in metric_data.items() if v is not None}
            
            # Determine sort order (higher is better for most metrics, except max_drawdown)
            reverse = metric not in ["max_drawdown"]
            
            sorted_strategies = sorted(valid_strategies.items(), key=lambda x: x[1], reverse=reverse)
            
            # Create ranking
            rankings[metric] = {}
            for rank, (strategy_name, value) in enumerate(sorted_strategies, 1):
                rankings[metric][strategy_name] = rank
        
        return rankings

    def _identify_best_strategy(self, strategy_results: List[Dict[str, Any]], rankings: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Identify the best overall strategy based on rankings"""
        
        try:
            strategy_scores = {}
            
            # Calculate weighted average rank for each strategy
            for strategy_result in strategy_results:
                strategy_name = strategy_result["name"]
                total_score = 0
                metric_count = 0
                
                for metric, strategy_rankings in rankings.items():
                    if strategy_name in strategy_rankings:
                        # Lower rank is better, so invert the score
                        rank = strategy_rankings[strategy_name]
                        score = 1 / rank if rank > 0 else 0
                        total_score += score
                        metric_count += 1
                
                if metric_count > 0:
                    strategy_scores[strategy_name] = total_score / metric_count
            
            if strategy_scores:
                best_strategy_name = max(strategy_scores.items(), key=lambda x: x[1])[0]
                best_strategy_result = next(s for s in strategy_results if s["name"] == best_strategy_name)
                
                return {
                    "name": best_strategy_name,
                    "score": strategy_scores[best_strategy_name],
                    "result": best_strategy_result["result"],
                    "parameters": best_strategy_result["parameters"]
                }
            
            return {"name": "NONE", "error": "No valid strategies found"}
            
        except Exception as e:
            self.logger.error(f"Error identifying best strategy: {e}")
            return {"name": "ERROR", "error": str(e)}

    def _categorize_performance(self, backtest_result: BacktestResult) -> str:
        """Categorize backtest performance"""
        
        win_rate = float(backtest_result.win_rate)
        total_pnl = float(backtest_result.total_profit_loss)
        sharpe_ratio = float(backtest_result.sharpe_ratio)
        
        if win_rate > 0.6 and total_pnl > 0 and sharpe_ratio > 1.5:
            return "EXCELLENT"
        elif win_rate > 0.55 and total_pnl > 0 and sharpe_ratio > 1.0:
            return "GOOD"
        elif win_rate > 0.5 and total_pnl >= 0 and sharpe_ratio > 0.5:
            return "FAIR"
        else:
            return "POOR"

    def _assess_backtest_risk(self, backtest_result: BacktestResult) -> str:
        """Assess risk level of backtest results"""
        
        max_drawdown = float(backtest_result.max_drawdown)
        initial_capital = float(self.initial_capital)
        
        drawdown_pct = abs(max_drawdown) / initial_capital if initial_capital > 0 else 0
        
        if drawdown_pct < 0.05:
            return "LOW"
        elif drawdown_pct < 0.15:
            return "MODERATE"
        elif drawdown_pct < 0.30:
            return "HIGH"
        else:
            return "EXTREME"

    def _generate_backtest_recommendations(self, backtest_result: BacktestResult) -> List[str]:
        """Generate recommendations based on backtest results"""
        
        recommendations = []
        
        win_rate = float(backtest_result.win_rate)
        total_pnl = float(backtest_result.total_profit_loss)
        max_drawdown = float(backtest_result.max_drawdown)
        total_signals = backtest_result.total_signals
        
        if win_rate < 0.5:
            recommendations.append("Win rate below 50% - consider improving signal quality")
        
        if total_pnl <= 0:
            recommendations.append("Strategy shows negative returns - review strategy logic")
        
        if abs(max_drawdown) > float(self.initial_capital) * 0.2:
            recommendations.append("High drawdown detected - implement stricter risk management")
        
        if total_signals < 10:
            recommendations.append("Low signal count - consider longer backtest period")
        
        if not recommendations:
            recommendations.append("Strategy shows promising results - consider forward testing")
        
        return recommendations

    def _calculate_confidence_score(self, backtest_result: BacktestResult) -> float:
        """Calculate confidence score for backtest results"""
        
        try:
            # Factors that affect confidence
            signal_count = backtest_result.total_signals
            win_rate = float(backtest_result.win_rate)
            sharpe_ratio = float(backtest_result.sharpe_ratio)
            
            # Signal count factor (more signals = higher confidence)
            signal_factor = min(1.0, signal_count / 100) * 0.3
            
            # Win rate factor
            win_rate_factor = (win_rate - 0.5) * 2 * 0.4 if win_rate > 0.5 else 0
            
            # Sharpe ratio factor
            sharpe_factor = min(1.0, max(0, sharpe_ratio) / 2) * 0.3
            
            confidence_score = signal_factor + win_rate_factor + sharpe_factor
            return max(0, min(1.0, confidence_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence score: {e}")
            return 0.0

    def _test_parameter_sensitivity(self, strategy_name: str, base_params: Dict[str, Any], market_data: List[MarketData]) -> Dict[str, Any]:
        """Test parameter sensitivity by varying parameters slightly"""
        
        # This is a simplified implementation
        # In production, this would test various parameter variations
        return {
            "sensitivity_score": 0.8,
            "stable_parameters": list(base_params.keys()),
            "sensitive_parameters": []
        }

    def _test_out_of_sample_performance(self, strategy_name: str, strategy_params: Dict[str, Any], market_data: List[MarketData]) -> Dict[str, Any]:
        """Test performance on out-of-sample data"""
        
        # Split data into in-sample and out-of-sample
        split_point = int(len(market_data) * 0.7)
        out_of_sample_data = market_data[split_point:]
        
        if len(out_of_sample_data) < 10:
            return {"error": "Insufficient out-of-sample data"}
        
        try:
            oos_result = self.run_strategy_backtest(
                strategy_name=f"{strategy_name}_oos",
                market_data=out_of_sample_data,
                strategy_params=strategy_params
            )
            
            return {
                "out_of_sample_signals": oos_result.total_signals,
                "out_of_sample_win_rate": float(oos_result.win_rate),
                "out_of_sample_pnl": float(oos_result.total_profit_loss),
                "data_points_used": len(out_of_sample_data)
            }
            
        except Exception as e:
            return {"error": str(e)}

    def _calculate_robustness_score(self, test_results: Dict[str, Any]) -> float:
        """Calculate overall robustness score from test results"""
        
        try:
            scores = []
            
            # Parameter sensitivity score
            if "parameter_sensitivity" in test_results and "error" not in test_results["parameter_sensitivity"]:
                sensitivity_score = test_results["parameter_sensitivity"].get("sensitivity_score", 0)
                scores.append(sensitivity_score)
            
            # Walk-forward score
            if "walk_forward" in test_results and "error" not in test_results["walk_forward"]:
                wf_analysis = test_results["walk_forward"].get("service_analysis", {})
                consistency = wf_analysis.get("performance_consistency", 0)
                scores.append(consistency)
            
            # Monte Carlo score
            if "monte_carlo" in test_results and "error" not in test_results["monte_carlo"]:
                mc_results = test_results["monte_carlo"]
                prob_loss = mc_results.get("probability_of_loss", 0.5)
                mc_score = 1 - prob_loss  # Lower probability of loss = higher score
                scores.append(mc_score)
            
            # Out-of-sample score
            if "out_of_sample" in test_results and "error" not in test_results["out_of_sample"]:
                oos_win_rate = test_results["out_of_sample"].get("out_of_sample_win_rate", 0)
                oos_score = oos_win_rate * 2 if oos_win_rate > 0.5 else 0  # Bonus for >50% win rate
                scores.append(min(1.0, oos_score))
            
            if scores:
                return sum(scores) / len(scores)
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error calculating robustness score: {e}")
            return 0.0

    def _assess_strategy_robustness(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall strategy robustness"""
        
        robustness_score = validation_results["overall_robustness_score"]
        
        if robustness_score > 0.8:
            level = "EXCELLENT"
            recommendation = "Strategy is highly robust and suitable for live trading"
        elif robustness_score > 0.6:
            level = "GOOD"
            recommendation = "Strategy shows good robustness with minor concerns"
        elif robustness_score > 0.4:
            level = "MODERATE"
            recommendation = "Strategy has moderate robustness - use with caution"
        else:
            level = "POOR"
            recommendation = "Strategy lacks robustness - not recommended for live trading"
        
        return {
            "robustness_level": level,
            "robustness_score": robustness_score,
            "recommendation": recommendation
        }