# Event Contract Trading System - Backend

FastAPI-based backend service for the Event Contract Trading System.

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Python**: 3.11+
- **Database**: PostgreSQL with SQLAlchemy
- **Time Series**: InfluxDB for market data
- **Cache**: Redis
- **Testing**: pytest with asyncio support

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Development dependencies
pip install -e ".[dev]"
```

## Development

```bash
# Run the development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Format code
black .
isort .

# Lint code
flake8 .
```

## Project Structure

```
backend/
├── src/
│   ├── api/           # API endpoints
│   ├── models/        # Data models
│   ├── services/      # Business logic
│   ├── lib/           # Core libraries
│   ├── database/      # Database connections
│   ├── middleware/    # Middleware components
│   ├── websocket/     # WebSocket handlers
│   ├── cli/           # CLI tools
│   ├── config/        # Configuration
│   └── main.py        # FastAPI application
├── tests/
│   ├── contract/      # Contract tests
│   ├── integration/   # Integration tests
│   └── unit/          # Unit tests
├── migrations/        # Database migrations
└── seeds/            # Development data
```