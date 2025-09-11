# Event Contract Trading System API

Version: 0.1.0

Base URL: `/api/v1`

## Health
- GET `/api/v1/health` → `{ status, checks, timestamp }`

## Signals
- GET `/api/v1/signals`
  - Query: `symbol?`, `confidence? (LOW|MEDIUM|HIGH)`, `limit? (1..100)`, `since? (ISO-8601)`
  - 200: `{ signals: [], total_count: number, has_more: boolean }`

- POST `/api/v1/signals/generate`
  - Body: `{ symbol: string, force_calculation?: boolean }`
  - 201: TradingSignal JSON `{ id, timestamp, symbol, direction, predicted_probability, confidence_level, expiry_time, ... }`

- GET `/api/v1/signals/{signal_id}`
  - 200: TradingSignal JSON
  - 404: unknown id; 400: invalid UUID

### WebSocket: `/ws/signals/{symbol}`
- Subscribes to live signal events for a symbol (pattern: `^[A-Z]{3,}USDT$`)
- Message schema (when used): `{ id, symbol, direction, predicted_probability, confidence_level, expiry_time }`

## Market Data
- GET `/api/v1/market-data/{symbol}`
  - Query: `interval (1m|5m|15m|1h)`, `limit (1..1000)`
  - 200: `{ symbol, interval, data: [{ timestamp, open_price, high_price, low_price, close_price, volume, quote_volume?, trade_count? }] }`

- POST `/api/v1/market-data/stream`
  - Body: `{ symbol: string, interval?: "1m"|"5m"|"15m"|"1h", client_id?: string }`
  - 201: `{ stream_id, symbol, status }`

### WebSocket: `/ws/market-data/{symbol}`
- Subscribes to live market data updates
- Message schema: `{ symbol, timestamp, price, volume }`

## Risk Parameters
- GET `/api/v1/risk-parameters`
  - 200: `{ user_id, max_bet_size, max_daily_bets, max_parallel_positions, min_probability_edge, frequency_limit_minutes, max_daily_loss }`

- PUT `/api/v1/risk-parameters`
  - Body: Partial update of the same fields
  - 200: Updated object

## Backtests
- POST `/api/v1/backtests`
  - Body: `{ strategy_name: string, start_date: YYYY-MM-DD, end_date: YYYY-MM-DD, symbol: string, initial_balance?: number|string }`
  - 202: `{ backtest_id, status (PENDING|RUNNING|QUEUED), created_at }`

- GET `/api/v1/backtests/{id}`
  - 200: `{ backtest_id, status, strategy_name, results: { total_trades, win_rate, total_return }, summary }`

- GET `/api/v1/backtests`
  - Query: `strategy_name?`, `limit? (1..100)`
  - 200: `{ results: [{ backtest_id, status, strategy_name }] }`

## Metrics
- GET `/api/v1/metrics/performance`
  - Query: `start_date? (YYYY-MM-DD)`, `end_date? (YYYY-MM-DD)`
  - 200: `{ metrics: PerformanceMetrics[], summary: { overall_win_rate, total_profit_loss, best_day, worst_day } }`

### WebSocket: `/ws/alerts`
- Subscribes to system or risk alerts
- Message schema: `{ level, message, timestamp, context? }`

## Authentication
- Current middleware is non-enforcing for development; include `Authorization` header when available.

## Notes
- All timestamps use ISO 8601 (UTC).
- Numeric types may be serialized as strings where precision matters (e.g., Decimal).
- See contract tests in `backend/tests/contract/` for precise schema expectations.
