# event-contract-v1 Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-09-10

## Active Technologies
- Python 3.11+ (FastAPI backend, pandas/numpy data analysis, pytest testing)
- React + TailwindCSS (dashboard frontend) 
- PostgreSQL + Time-series DB (data storage)
- WebSocket libraries (real-time data streaming)

## Project Structure
```
backend/          # FastAPI backend services
frontend/         # React dashboard UI  
tests/           # Test suites
specs/           # Feature specifications
```

## Commands
```bash
# Python backend
uv run pytest
uv run ruff check .

# Frontend (when implemented)
npm test
npm run lint
```

## Code Style
- Python: Follow PEP 8, use type hints, uv for dependency management
- React: Standard conventions with TypeScript
- Testing: pytest for Python, comprehensive test coverage

## Recent Changes
- 001-1-10-80: Added event contract trading system with Python backend, React frontend, and real-time data processing

<!-- MANUAL ADDITIONS START -->
- use uv manage python project, don't use requirements.txt, use pyproject.toml to manage deps
<!-- MANUAL ADDITIONS END -->