-- T080: Database migration scripts - Indexes

CREATE INDEX IF NOT EXISTS idx_event_contracts_symbol ON trading.event_contracts(symbol);
CREATE INDEX IF NOT EXISTS idx_event_contracts_expiry ON trading.event_contracts(expiry_time);
CREATE INDEX IF NOT EXISTS idx_risk_parameters_user ON trading.risk_parameters(user_id);
CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy ON trading.backtest_results(strategy_name);
CREATE INDEX IF NOT EXISTS idx_backtest_trades_result ON trading.backtest_trades(backtest_result_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON trading.performance_metrics(date);

