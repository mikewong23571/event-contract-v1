# Event Contract Trading System - Development Tools
# Unified commands for linting, formatting, and quality checks

.PHONY: help format lint type-check test clean install-tools dev stop down shutdown

# Default target
help:
	@echo "Event Contract Trading System - Development Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make format       - Format all code (Python: black, isort; JS/TS: prettier)"
	@echo "  make lint         - Lint all code (Python: flake8; JS/TS: eslint)"
	@echo "  make type-check   - Type check all code (Python: mypy; TS: tsc)"
	@echo "  make test         - Run all tests"
	@echo "  make clean        - Clean build artifacts and caches"
	@echo "  make install-tools - Install development tools"
	@echo "  make dev          - Start infra (Compose) and all app services (Procfile.dev)"
	@echo ""
	@echo "Component-specific:"
	@echo "  make format-python    - Format Python code only"
	@echo "  make format-frontend  - Format frontend code only"
	@echo "  make lint-python      - Lint Python code only"
	@echo "  make lint-frontend    - Lint frontend code only"

# Install development tools
install-tools:
	@echo "Syncing Python project dependencies with uv (including dev extras)..."
	cd backend && uv sync --extra dev
	cd backtesting && uv sync --extra dev
	cd runtime && uv sync --extra dev
	cd notifications && uv sync --extra dev
	@echo "Installing Node.js development tools..."
	cd frontend && npm install --save-dev eslint prettier @typescript-eslint/parser @typescript-eslint/eslint-plugin prettier-plugin-tailwindcss

# Format all code
format: format-python format-frontend
	@echo "All code formatted successfully!"

format-python:
	@echo "Formatting Python code with black and isort (via uv)..."
	cd backend && uv run black . && uv run isort .
	cd backtesting && uv run black . && uv run isort .
	cd runtime && uv run black . && uv run isort .
	cd notifications && uv run black . && uv run isort .

format-frontend:
	@echo "Formatting frontend code with prettier..."
	cd frontend && npx prettier --write .

# Lint all code
lint: lint-python lint-frontend
	@echo "All linting completed!"

lint-python:
	@echo "Linting Python code with flake8 (via uv)..."
	cd backend && uv run flake8 .
	cd backtesting && uv run flake8 .
	cd runtime && uv run flake8 .
	cd notifications && uv run flake8 .

lint-frontend:
	@echo "Linting frontend code with eslint..."
	cd frontend && npx eslint . --ext .js,.jsx,.ts,.tsx

# Type checking
type-check: type-check-python type-check-frontend
	@echo "All type checking completed!"

type-check-python:
	@echo "Type checking Python code with mypy (via uv)..."
	cd backend && uv run mypy src/
	cd backtesting && uv run mypy src/
	cd runtime && uv run mypy src/
	cd notifications && uv run mypy src/

type-check-frontend:
	@echo "Type checking frontend code with tsc..."
	cd frontend && npx tsc --noEmit

# Run tests
test:
	@echo "Running all tests (via uv/npm)..."
	cd backend && uv run pytest
	cd backtesting && uv run pytest
	cd runtime && uv run pytest
	cd notifications && uv run pytest
	cd frontend && npm run test

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts and caches..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	rm -rf backend/dist/ backend/build/ backend/*.egg-info/
	rm -rf backtesting/dist/ backtesting/build/ backtesting/*.egg-info/
	rm -rf runtime/dist/ runtime/build/ runtime/*.egg-info/
	rm -rf notifications/dist/ notifications/build/ notifications/*.egg-info/
	cd frontend && rm -rf .next/ dist/ build/ node_modules/.cache/

# Shortcuts for quick development
fix: format lint
	@echo "Code formatted and linted!"

check: lint type-check
	@echo "Code checked for issues!"

ci: format lint type-check test
	@echo "Full CI pipeline completed!"

# Start all services for development: infra via Docker Compose, apps via Procfile.dev
dev:
	@echo "Starting infrastructure (Docker Compose) ..."
	docker compose up -d
	@echo "Starting app processes via Procfile.dev using uvx (no global install)..."
	uvx honcho start -f Procfile.dev

# Stop only app processes started by honcho (best-effort)
stop:
	@echo "Stopping app processes (honcho-managed) ..."
	-pkill -f "honcho start -f Procfile.dev" || true
	-pkill -f "uvicorn src.main:app" || true
	-pkill -f "uv run -m src.main" || true
	-pkill -f "npm run dev" || true
	@echo "App processes stopped (if they were running)."

# Stop only infrastructure containers
down:
	@echo "Stopping infrastructure (Docker Compose) ..."
	docker compose down

# One-click: stop app processes and infrastructure
shutdown:
	@echo "Shutting down app processes and infrastructure ..."
	$(MAKE) stop
	$(MAKE) down
	@echo "All services stopped."
