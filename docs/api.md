# Event Contract Trading System API

Version: 0.1.0

Base URL: `/api/v1`

## Health
- GET `/api/v1/health` → `{ status, uptime_seconds, timestamp }`

## Signals
- GET `/api/v1/signals`
  - Query: `symbol?`, `limit?`
  - 200: `[{ id, timestamp, symbol, direction, predicted_probability, confidence_level, expiry_time, strategy_version }]`

- POST `/api/v1/signals/generate`
  - Body: `{ symbol: string, expiry_minutes?: number }`
  - 200: `{ signal_id, symbol, direction, predicted_probability, confidence_level, expiry_time }`

### WebSocket: `/ws/signals`
- Subscribes to live signal events
- Message schema: `{ id, symbol, direction, predicted_probability, confidence_level, expiry_time }`

## Market Data
- GET `/api/v1/market-data`
  - Query: `symbol`, `start_time?`, `end_time?`, `limit?`
  - 200: `[{ timestamp, open_price, high_price, low_price, close_price, volume, source }]`

- POST `/api/v1/market-data/stream`
  - Body: `{ symbol: string, action: "start" | "stop" }`
  - 202: `{ status, symbol }`

### WebSocket: `/ws/market-data`
- Subscribes to live market data updates
- Message schema: `{ symbol, timestamp, price, volume }`

## Risk Parameters
- GET `/api/v1/risk-parameters`
  - 200: `{ user_id, max_bet_size, max_daily_bets, max_parallel_positions, min_probability_edge, frequency_limit_minutes, max_daily_loss }`

- PUT `/api/v1/risk-parameters`
  - Body: same as above
  - 200: Updated object

## Backtests
- POST `/api/v1/backtests`
  - Body: `{ strategy_name, market_data: [...], strategy_params: {...} }`
  - 202: `{ id, status }`

- GET `/api/v1/backtests/{id}`
  - 200: `{ id, strategy_name, total_signals, win_rate, total_profit_loss, created_at, trades: [...], metrics: {...} }`

### WebSocket: `/ws/alerts`
- Subscribes to system or risk alerts
- Message schema: `{ level, message, timestamp, context? }`

## Authentication
- Current middleware is non-enforcing for development; include `Authorization` header when available.

## Notes
- All timestamps use ISO 8601 (UTC).
- Numeric types may be serialized as strings where precision matters (e.g., Decimal).
- See contract tests in `backend/tests/contract/` for precise schema expectations.

