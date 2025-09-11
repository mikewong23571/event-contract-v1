# Repository Guidelines

This document is a concise contributor guide for the Event Contract Trading System.

## Project Structure & Module Organization
- Root: shared config (`.env`, `Makefile`, `docker-compose*.yml`), docs.
- `backend/` FastAPI API + WebSocket; `runtime/` real‑time engine; `backtesting/` analysis; `notifications/` alerts; `frontend/` Next.js dashboard.
- Source in `src/`; tests in `tests/` (unit/integration/e2e). Assets live in component folders.

## Build, Test, and Development Commands
- Install deps (all Python via uv): `make install-tools`
- Start dev (infra + apps via honcho): `make dev`
- Stop services: `make shutdown` (or `make stop` / `make down`)
- Format, Lint, Types, Tests: `make format | lint | type-check | test | ci`
- Component examples: `cd backend && uv run uvicorn src.main:app --reload`, `cd frontend && npm run dev`
- Compose: use `docker compose ...` (not `docker-compose`).

## Coding Style & Naming Conventions
- Python: Black + isort, Flake8, Mypy (py311). Keep modules small; functions snake_case; classes PascalCase; files snake_case.
- TypeScript/JS: ESLint + Prettier; React with Next.js App Router.
- Keep logs structured; avoid global state; prefer pure functions in libs.

## Testing Guidelines
- Python: pytest (asyncio where needed), run with `uv run pytest`. Test files: `tests/**/test_*.py`.
- Frontend: Jest/RTL (`npm test`). Add integration tests for API interactions where feasible.
- Aim for meaningful coverage on logic paths; prefer contract/integration tests for service boundaries.

## Commit & Pull Request Guidelines
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`.
- PRs must include: scope/intent, linked issues, test evidence (commands/output), and user‑visible changes (screenshots for UI).
- Keep diffs focused; update docs when behavior or commands change.

## Security & Configuration Tips
- Never commit secrets. Use `.env` locally; only `NEXT_PUBLIC_*` are exposed to the browser.
- Follow principle of least privilege; validate inputs; prefer structured logging.

## Agent‑Specific Instructions
- Python deps are managed with uv; do not add `requirements.txt`. Use `pyproject.toml` + `uv.lock` and `uv add/remove`.
- Adhere to `/memory/constitution.md` (library‑first, CLI protocol, TDD, observability, versioning).
