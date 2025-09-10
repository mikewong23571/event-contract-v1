-- T080: Database migration scripts - Create core relational tables

-- Ensure extensions and schemas are present (idempotent)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE SCHEMA IF NOT EXISTS trading;

-- Event Contracts
CREATE TABLE IF NOT EXISTS trading.event_contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_id VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    strike_price NUMERIC(18,8) NOT NULL,
    expiry_time TIMESTAMPTZ NOT NULL,
    payout_ratio NUMERIC(6,4) NOT NULL,
    implied_probability NUMERIC(6,4) NOT NULL,
    status VARCHAR(20) NOT NULL,
    settlement_price NUMERIC(18,8),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Risk Parameters
CREATE TABLE IF NOT EXISTS trading.risk_parameters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL,
    max_bet_size NUMERIC(18,8) NOT NULL,
    max_daily_bets INT NOT NULL,
    max_parallel_positions INT NOT NULL,
    min_probability_edge NUMERIC(6,4) NOT NULL,
    frequency_limit_minutes INT NOT NULL,
    max_daily_loss NUMERIC(18,8) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Backtest Results
CREATE TABLE IF NOT EXISTS trading.backtest_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_name VARCHAR(100) NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    total_signals INT NOT NULL,
    successful_signals INT NOT NULL,
    win_rate NUMERIC(6,4) NOT NULL,
    total_profit_loss NUMERIC(18,8) NOT NULL,
    max_drawdown NUMERIC(18,8) NOT NULL,
    sharpe_ratio NUMERIC(10,6) NOT NULL,
    parameters JSONB,
    execution_mode VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Backtest Trades
CREATE TABLE IF NOT EXISTS trading.backtest_trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backtest_result_id UUID NOT NULL REFERENCES trading.backtest_results(id) ON DELETE CASCADE,
    signal_timestamp TIMESTAMPTZ NOT NULL,
    direction VARCHAR(10) NOT NULL,
    entry_price NUMERIC(18,8) NOT NULL,
    exit_price NUMERIC(18,8) NOT NULL,
    bet_amount NUMERIC(18,8) NOT NULL,
    profit_loss NUMERIC(18,8) NOT NULL,
    was_successful BOOLEAN NOT NULL,
    contract_duration_minutes INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Performance Metrics (daily aggregation)
CREATE TABLE IF NOT EXISTS trading.performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    total_signals_generated INT NOT NULL,
    total_signals_executed INT NOT NULL,
    daily_win_rate NUMERIC(6,4) NOT NULL,
    daily_profit_loss NUMERIC(18,8) NOT NULL,
    avg_signal_latency_ms INT NOT NULL,
    system_uptime_percentage NUMERIC(6,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

