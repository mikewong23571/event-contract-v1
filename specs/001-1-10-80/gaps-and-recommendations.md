# Gaps & Recommendations — Event Contract Trading System

Last updated: 2025-09-11

This document consolidates current gaps found when comparing the implementation to the spec/contracts, and tracks resolved items. It is organized by component/boundary for quick actionability.

## Current Gaps

### Backend — REST API
- RESOLVED: GET `/api/v1/signals/{signal_id}` implemented
  - Implemented in `backend/src/api/signals.py` with in-memory registry and explicit 400/404 handling.
  - Included persistence from POST `/signals/generate` for retrieval.

- RESOLVED: GET `/api/v1/backtests`
  - Implemented in `backend/src/api/backtests.py` with `strategy_name?` and `limit?` support.
  - Returns `{ results: [...] }` with minimal fields per contract.

- RESOLVED: GET `/api/v1/metrics/performance`
  - Implemented in `backend/src/api/metrics.py`; wired in `src/main.py`.
  - Returns `{ metrics, summary }` mapped from `monitoring/metrics.py`.

### Backend — WebSocket API
- RESOLVED: `/ws/system-status` channel implemented
  - Implemented in `backend/src/websocket/system_status_ws.py` with periodic system status broadcasts.
  - Streams system health, component status, and metrics per AsyncAPI schema.

- RESOLVED: `/ws/client/commands` and `/ws/client/responses` channels implemented
  - Implemented in `backend/src/websocket/client_commands_ws.py`.
  - Handles subscribe/unsubscribe/get_status/update_risk_params/generate_signal commands per contract.

### Frontend ↔ Backend Contract Mismatches
- RESOLVED: Frontend API adapter layer created
  - Created `frontend/src/services/apiAdapter.ts` to bridge contract mismatches.
  - Adapts backend response formats to frontend expected envelopes.
  - Handles endpoint path/shape differences (market data, pagination, risk parameters).
  - Transforms backend field names to frontend expected formats.

- Docs inconsistency
  - RESOLVED: Updated `docs/api.md` to document `/ws/market-data/{symbol}` and added new REST endpoints.

### CLI (Constitutional) — Library-level tools
- RESOLVED: CLI flags standardized across library CLIs
  - Updated `backend/src/lib/signal_generation/cli.py` with `--version` and `--format {json,text}` flags.
  - Added structured output utilities to support both text and JSON formats.
  - Existing CLIs in backtesting and notifications already had `--version`; added `--format` flag.

### Observability & Metrics
- REST exposure for performance metrics missing
  - Collector exists; no endpoint.
  - Action: implement GET `/api/v1/metrics/performance` and (optional) `/metrics` Prometheus text.

### Runtime Integration
- RESOLVED: Real-time engine wired to backend outputs
  - Created `runtime/src/publishers/signal_publisher.py` to bridge runtime and backend.
  - Updated `runtime/src/main.py` to integrate signal publishing with detection engine.
  - Runtime signals now persist to backend API and can reach dashboard via WebSocket.

## Recommendations (Actionable Tasks)
- Backend
  - Add GET `/api/v1/signals/{signal_id}` in `backend/src/api/signals.py`.
  - Add GET `/api/v1/backtests` in `backend/src/api/backtests.py`.
  - Add GET `/api/v1/metrics/performance` in new `backend/src/api/metrics.py` mapping from `monitoring/metrics.py`.
  - WebSocket: implement `/ws/system-status`, `/ws/client/commands`, `/ws/client/responses` under `backend/src/websocket/`.
  - Update `docs/api.md` for WS market-data path and new endpoints.

- Frontend
  - Update `src/services/api.ts` to match backend paths and response shapes; add integration tests for API calls.

- CLI
  - Standardize library CLIs with `--version` and `--format {json,text}`; ensure outputs are machine-readable when `json`.

- Runtime
  - Bridge runtime signal outputs to backend WS or persistence; add minimal integration for end-to-end demo.

## Resolved Since Previous Update
- T051 POST `/api/v1/backtests` implemented
  - `backend/src/api/backtests.py` adds POST with 202 Accepted and `{ backtest_id, status, created_at }`.

- T072 Backtest report generator path mismatch fixed
  - Added wrapper: `backtesting/src/generators/report_generator.py` re-exporting library implementation.

- API docs alignment (partial)
  - `docs/api.md` now documents signals/market-data/risk/backtests/health; remaining WS path adjustment pending (see gaps above).

- T101 GET `/api/v1/signals/{signal_id}` implemented — local commit — 2025-09-11
- T102 GET `/api/v1/backtests` implemented — local commit — 2025-09-11
- T103 GET `/api/v1/metrics/performance` implemented — local commit — 2025-09-11
- Docs: WS market-data path corrected and new endpoints documented — local commit — 2025-09-11
- T104 WebSocket `/ws/system-status` channel implemented — local commit — 2025-09-11
- T105 WebSocket `/ws/client/commands` and `/ws/client/responses` channels implemented — local commit — 2025-09-11
- T106 Frontend API adapter layer created for contract mismatches — local commit — 2025-09-11
- T107 CLI flags standardized across library CLIs with `--version` and `--format` — local commit — 2025-09-11
- T108 Runtime engine wired to backend outputs via signal publisher — local commit — 2025-09-11

## Optional Improvements
- Ensure explicit 400 (vs 422) responses on validation across endpoints (consistency is mostly in place).
- Add “How to run with uv” quick notes into each Python component README (root README already covers this).
- Centralize version source for CLIs (avoid hard-coded defaults; read from package metadata when available).
