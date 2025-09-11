# AI Agent Prompt: Maintain and Drive `gaps-and-recommendations.md`

## Objective
- Align the codebase with the specs by executing and maintaining `specs/001-1-10-80/gaps-and-recommendations.md` as the single source of truth for gaps, actions, and status.

## Context
- Repo rules: see `AGENTS.md` (uv-only, Make targets, code style, tests), `memory/constitution.md` (library-first, CLI protocol, TDD, observability, versioning).
- Specs: OpenAPI in `specs/001-1-10-80/contracts/*.yaml`, functional spec + models in `specs/001-1-10-80/spec.md` and `data-model.md`.
- Current gap log: `specs/001-1-10-80/gaps-and-recommendations.md`.

## Constraints
- Python deps via `uv` only; no `requirements.txt`.
- Run/format/lint via `Makefile`.
- Keep changes minimal and scoped; follow file organization and naming conventions.
- Don’t commit secrets; keep 400 vs 422 behaviors consistent where enforced.
- Prefer tests-first where feasible (contract/integration/unit).

## Deliverables
- Implement fixes for recorded gaps (REST/WS endpoints, CLI flags, frontend contract adapters, metrics exposure, runtime wiring).
- Update `docs/api.md` and `specs/…/contracts/*` if behavior/paths change.
- Add or update tests validating fixes.
- Update `specs/001-1-10-80/gaps-and-recommendations.md`:
  - Move resolved items to “Resolved Since Previous Update”.
  - Keep “Current Gaps” accurate with acceptance criteria and owner.
  - Record recommendations as actionable, checkable tasks.

## Prioritized Backlog (from Current Gaps)
1) Backend REST
   - GET `/api/v1/signals/{signal_id}`
   - GET `/api/v1/backtests`
   - GET `/api/v1/metrics/performance` (map from `monitoring/metrics.py`)

2) Backend WebSocket
   - `/ws/system-status`
   - `/ws/client/commands`
   - `/ws/client/responses`

3) Frontend Contract Adapters
   - Align `frontend/src/services/api.ts` to backend paths and response shapes or add adapters.

4) CLI (Constitutional)
   - Standardize `--version` and `--format {json,text}` in:
     - `backend/src/lib/signal_generation/cli.py`
     - `backtesting/src/lib/backtesting_engine/cli.py`
     - `notifications/src/lib/notification_manager/cli.py`

5) Observability
   - Expose metrics via REST; optionally add `/metrics` (Prometheus text) if non-invasive.

6) Runtime Integration
   - Publish detected signals to backend (WS or persistence) for end-to-end visibility.

## Acceptance Criteria (per item)
- GET `/signals/{signal_id}`: 200 with full TradingSignal; 404 unknown; 400 invalid UUID.
- GET `/backtests`: 200 with `{ results: [...] }` per OpenAPI; supports `strategy_name?` and `limit?`.
- GET `/metrics/performance`: 200 with `{ metrics: [...], summary: {...} }` aligned to OpenAPI types.
- WS `/system-status`: sends periodic JSON matching AsyncAPI schema; graceful close.
- WS `/client/commands` + `/client/responses`: accepts `subscribe|unsubscribe|get_status|update_risk_params|generate_signal`; responds with correlated `request_id` and status.
- Library CLIs: `--help --version --format` present; JSON output when requested; non-zero exit on error.
- Frontend ApiClient: compiles, tests pass, adapters return data matching component expectations without breaking existing tests.
- Docs updated; tests passing via `make test`.

## Workflow
For each gap:
1. Write/adjust tests first (contract/integration/unit) to encode expected behavior (if missing).
2. Implement minimal code to pass tests; keep style/structure consistent.
3. Run format/lint/types/tests with `make fix`, `make check`, `make test`.
4. Update `docs/api.md` if any API contract visible to consumers changed.
5. Update `specs/001-1-10-80/gaps-and-recommendations.md`: move the item to “Resolved” with a one-line reference (paths/PR/commit).
6. If ambiguous, add a “Clarification Needed” bullet with concrete questions.

## Editing The Gap Log
Use this structure per gap in `gaps-and-recommendations.md`:
- Title: short and verb-first (e.g., “Add GET /api/v1/backtests”).
- Spec Reference: file/path and section.
- Current Behavior: 1–2 lines.
- Target Behavior: 1–2 lines.
- Acceptance: bullet list of verifiable checks.
- Tasks: bullets with file paths.
- Status: Todo/In-Progress/Done + date.

Move completed items to “Resolved Since Previous Update” with:
- `Resolved: <title> — <commit or PR link> — <date>`

## Commands
- Install: `make install-tools`
- Dev: `make dev` (Ctrl+C to stop) or `make shutdown`
- Format/Lint/Types/Tests: `make fix`, `make check`, `make test`
- Component tests (examples):
  - Backend: `cd backend && uv run pytest -q`
  - Frontend: `cd frontend && npm test -s`
  - Runtime/Backtesting/Notifications: `cd <component> && uv run pytest -q`

## Style
- Python: Black + isort; Flake8; mypy on `src/`.
- TS/JS: ESLint + Prettier; Next.js App Router.
- Keep modules small; functions snake_case; classes PascalCase; files snake_case.

## Out of Scope
- Unrelated refactors, broad renames, or infra changes without a linked gap.
- Adding new external dependencies unless justified in the gap log.

## Success
- All “Current Gaps” are either implemented and moved to “Resolved” with tests/docs, or documented with clear clarifications/blockers.
- `make ci` passes locally.
- Docs are consistent with code (OpenAPI/AsyncAPI vs implementation vs `docs/api.md`).

