# Configuration Guide

This guide explains how to configure the Event Contract Trading System using environment variables (.env), how each component reads configuration, and best practices for development and production.

## Quick Start

1) Copy the example file and edit values
- cp .env.example .env
- Update credentials and URLs as needed

2) Start infrastructure
- docker compose up -d

3) Start all app processes (Procfile.dev)
- make dev  # uses uvx honcho and loads .env automatically

Honcho/foreman reads `.env` at repository root and exports variables to all processes in Procfile.dev. Python services also read `.env` directly via Pydantic Settings.

## How configuration is loaded

- Backend (FastAPI): `backend/src/config/settings.py`
  - Pydantic Settings loads from process env and `.env`, `.env.local` (root); case-insensitive keys; explicit aliases map to expected variable names.
  - DSNs are derived from `DATABASE_URL` if set, otherwise from `POSTGRES_*` fields.

- Runtime engine: `runtime/src/config/settings.py`
  - Pydantic Settings loads from process env and `.env` (root).

- Notifications service: `notifications/src/config/settings.py`
  - Pydantic Settings loads from process env and `.env` (root). Sensitive fields use `SecretStr`.

- Frontend (Next.js):
  - Receives environment from honcho (process env) when started via `make dev`.
  - Additionally supports its own `frontend/.env*` files if you run it standalone.
  - Only variables prefixed with `NEXT_PUBLIC_` are automatically exposed to the browser.

## Key environment variables

The repository includes `.env.example` with all supported keys. Commonly used variables:

- Application
  - `ENVIRONMENT` (development|staging|production)
  - `DEBUG` (true|false)
  - `LOG_LEVEL` (DEBUG|INFO|WARNING|ERROR)
  - `LOG_FORMAT` (json|text)

- Backend API
  - `BACKEND_HOST`, `BACKEND_PORT`, `CORS_ORIGINS`, `CORS_CREDENTIALS`
  - Auth (optional): `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`

- Databases
  - Postgres: `DATABASE_URL` or `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
  - Redis: `REDIS_URL` or `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`
  - InfluxDB: `INFLUXDB_URL`, `INFLUXDB_TOKEN`, `INFLUXDB_ORG`, `INFLUXDB_BUCKET`

- Binance API
  - `BINANCE_API_KEY`, `BINANCE_SECRET_KEY`, `BINANCE_TESTNET`, `BINANCE_BASE_URL`

- Frontend (Next.js)
  - `NEXT_PUBLIC_API_BASE_URL` (e.g., http://localhost:8000/api/v1)
  - `NEXT_PUBLIC_WS_URL` (e.g., ws://localhost:8000)
  - `NEXT_PUBLIC_ENVIRONMENT` (development|production)

- Runtime engine
  - `SIGNAL_INTERVAL`, `MIN_CONFIDENCE`, `TRADING_SYMBOLS`

- Notifications
  - Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_IDS`, `TELEGRAM_ENABLED`
  - Feishu: `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_WEBHOOK_URL`, `FEISHU_ENABLED`
  - Email: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `SMTP_FROM_EMAIL`, `EMAIL_RECIPIENTS`, `EMAIL_ENABLED`
  - Celery/Redis: `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`

- Monitoring/metrics
  - `METRICS_ENABLED`, `METRICS_PORT`, `PROMETHEUS_GATEWAY`

## Minimal .env for local dev

```
# App
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
LOG_FORMAT=json

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
CORS_ORIGINS=http://localhost:3000
CORS_CREDENTIALS=true

# Databases
DATABASE_URL=postgresql://dev_user:dev_password@localhost:5432/event_contract_dev
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=dev_token_for_development_only
INFLUXDB_ORG=trading
INFLUXDB_BUCKET=market_data
REDIS_URL=redis://localhost:6379/0

# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development

# Runtime
TRADING_SYMBOLS=BTCUSDT,ETHUSDT
SIGNAL_INTERVAL=1.0
MIN_CONFIDENCE=0.6

# Notifications (optional)
TELEGRAM_ENABLED=false
FEISHU_ENABLED=false
EMAIL_ENABLED=false
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

## How it works (flow)

- When you run `make dev`, honcho loads `.env` and exports variables to all processes defined in `Procfile.dev`.
- Python apps (backend/runtime/notifications) also load `.env` through Pydantic Settings at startup and apply component defaults if values are missing.
- The frontend receives `NEXT_PUBLIC_*` variables from process env and injects them at build/dev time; these are available via `process.env.NEXT_PUBLIC_*` and exposed to the browser.

## Per-environment overrides

- Local overrides: create `.env.local` at repository root to override values on your machine (ignored by Git), or `frontend/.env.local` if you run the frontend standalone.
- CI/Prod: prefer real environment variables set by your orchestrator (GitHub Actions, Docker/Compose, Kubernetes) instead of files.
- Compose: you can reference `${VARIABLES}` in `docker-compose.yml`/`.override.yml` to use values from `.env`.

## Secrets & best practices

- Do not commit secrets to Git. `.env` should be for development defaults only.
- Keep `.env.example` up-to-date to document required variables.
- Use per-environment `.env.local` files that are gitignored for developer machines.
- For production, use:
  - Docker secrets or Kubernetes Secrets for credentials
  - A secret manager (e.g., Vault, AWS Secrets Manager, GCP Secret Manager)
  - CI/CD to inject environment variables at deploy time
- Rotate keys regularly, especially API tokens (Binance, Telegram, Feishu).
- Use least privilege for database and API credentials per environment.

## Notes & tips

- Backend DSN logic: If `DATABASE_URL` is set, it’s used; otherwise a DSN is built from `POSTGRES_*`. Async SQLAlchemy uses `postgresql+asyncpg://...` under the hood.
- Redis DSN logic: If `REDIS_URL` is set, it’s used; otherwise it’s built from host/port/db.
- InfluxDB requires `INFLUXDB_TOKEN`; you can create an admin token in the UI or via env during container init.
- Frontend variables must use the `NEXT_PUBLIC_` prefix to be exposed to the browser.
- Procfile.dev + honcho ensures all services get the same configuration from root `.env` with a single command.

## Troubleshooting

- Frontend cannot reach API
  - Check `NEXT_PUBLIC_API_BASE_URL` and CORS (`CORS_ORIGINS`) in `.env` match the actual backend URL.

- InfluxDB auth errors
  - Verify `INFLUXDB_TOKEN`, `INFLUXDB_ORG`, and `INFLUXDB_BUCKET` values; confirm the token has the proper permissions.

- Redis/DB connection
  - Ensure containers are up (`docker compose ps`) and ports match `.env`.

- WebSockets issues
  - Verify `NEXT_PUBLIC_WS_URL` and that backend listens on the same host/port.
