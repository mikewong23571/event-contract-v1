# Gaps & Recommendations — Event Contract Trading System

Last updated: 2025-09-11

## Gaps
- T051 POST /api/v1/backtests is missing.
  - Tests expect 202 Accepted and JSON with `backtest_id`, `status`, `created_at`.
  - No `@router.post("/backtests")` in `backend/src/api/backtests.py`.

- T072 path mismatch for Backtest report generator.
  - Task path: `backtesting/src/generators/report_generator.py` (missing).
  - Current implementation exists under `backtesting/src/lib/backtesting_engine/report_generator.py`.

- T103 API docs out of sync with implementation/tests.
  - GET /api/v1/signals: docs show array; implementation/tests use `{ signals, total_count, has_more }`.
  - GET /api/v1/market-data: docs show query `symbol`; implementation/tests use path `/api/v1/market-data/{symbol}` and `interval/limit` params.
  - Health endpoint: docs list `uptime_seconds`; implementation returns `{ status, checks, timestamp }`.
  - WS signals path should include `/ws/signals/{symbol}`.

- Task status drift in tasks.md.
  - T065–T067 (runtime components) are implemented but are still unchecked in tasks.md.

- Library-local CLIs lack constitutional flags.
  - Library CLIs under `backend/src/lib/*/cli.py` don’t uniformly support `--version` and `--format`.
  - Top-level CLIs (backend/src/cli/*, backtesting/src/cli/backtest_cli.py, notifications/src/cli/notification_cli.py) already comply.

- Minor: Duplicate router include in backend app.
  - `backend/src/main.py` includes `backtests_router` twice.

- README references updated to use `uv` instead of `pip -r`.

## Recommendations
- Implement T051 endpoint in `backend/src/api/backtests.py`:
  - Add `@router.post("/backtests", status_code=202)` that validates input (`strategy_name`, `start_date`, `end_date`, `symbol`, `initial_balance?`) and returns `{ backtest_id, status, created_at }`.

- Address T072 by adding a thin wrapper:
  - Create `backtesting/src/generators/report_generator.py` that re-exports/forwards to `lib/backtesting_engine/report_generator.py`.

- Update API docs (T103) in `docs/api.md`:
  - Align signals response shape to `{ signals, total_count, has_more }`.
  - Document `GET /api/v1/market-data/{symbol}` with `interval` and `limit` params.
  - Update health response to `{ status, checks, timestamp }` (or implement `uptime_seconds`).
  - Document WebSocket path `/ws/signals/{symbol}`.

- Update task checkboxes in `specs/001-1-10-80/tasks.md` for T065–T067 to reflect completion.

- Harmonize library-local CLIs with constitutional flags:
  - Add `--version` and `--format {json,text}` to CLIs under `backend/src/lib/*/cli.py` for consistency.

- Remove duplicate `backtests_router` include from `backend/src/main.py`.

- Update README to use `uv` instead of `pip -r`:
  - Example: `uv sync` (per component) and `uv run -m src.main` or `uv run pytest`.

## Optional Improvements
- Ensure all 400 vs 422 validation behaviors remain consistent across endpoints (already handled in most places).
- Add a short “How to run with uv” section to each Python component README for clarity.
