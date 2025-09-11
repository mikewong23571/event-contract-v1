# Event Contract Trading System - Runtime Engine

Real-time trading signal detection engine that processes live market data and generates probability-based trading signals.

## Tech Stack

- **Python**: 3.11+
- **WebSockets**: websockets, aiohttp for real-time communication
- **Market Data**: python-binance, ccxt for exchange connectivity
- **Data Processing**: pandas, numpy for real-time stream processing
- **Storage**: Redis (caching), InfluxDB (time-series data)
- **Monitoring**: structlog, prometheus-client
- **Testing**: pytest with asyncio and mocking

## Installation (uv)

```bash
# Install dependencies (uv)
uv sync

# Include dev extras (tests, linters, etc.)
uv sync --extra dev
```

## Usage

```bash
# Start runtime engine
runtime

# Start with custom configuration
runtime --config configs/production.env

# Start signal detector only
signal-detector --symbols BTCUSDT,ETHUSDT
```

## Repo Workflow (uv + Make)

- 推荐使用仓库根目录的 Make 命令统一操作：
  - `make dev` 启动基础设施与所有应用服务（通过 uvx honcho + Procfile.dev）
  - `make test` 统一运行测试
  - `make format` / `make lint` / `make type-check` 执行代码质量工具
  - 所有 Python 工具均通过 `uv run` 运行，无需全局安装

## Features

- **Real-time Market Data**: Live 1-minute K-line data processing from Binance
- **Signal Detection**: Probability-based trading signal generation
- **WebSocket Streaming**: Real-time data distribution to clients
- **Multi-symbol Support**: Concurrent monitoring of multiple trading pairs
- **Performance Monitoring**: Prometheus metrics and structured logging
- **Graceful Shutdown**: Signal handling for clean service termination
- **Configuration Management**: Environment-based configuration system

## Configuration

Configure via environment variables or `.env` file:

```bash
# Binance API credentials
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
BINANCE_TESTNET=true

# WebSocket settings
WEBSOCKET_HOST=0.0.0.0
WEBSOCKET_PORT=8001

# Trading symbols (comma-separated)
TRADING_SYMBOLS=BTCUSDT,ETHUSDT,BNBUSDT

# Signal detection
SIGNAL_INTERVAL=1.0
MIN_CONFIDENCE=0.6

# Database connections
REDIS_URL=redis://localhost:6379/0
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_influx_token

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Project Structure

```
runtime/
├── src/
│   ├── main.py              # Application entry point
│   ├── config/              # Configuration management
│   ├── processors/          # Market data processors
│   ├── engines/             # Signal detection engines
│   ├── calculators/         # Probability calculators
│   ├── clients/             # External API clients
│   └── monitoring/          # Metrics and health checks
├── tests/
│   ├── integration/         # Integration tests
│   └── unit/               # Unit tests
└── configs/                # Configuration files
```

## Performance

- **Latency**: Sub-second signal generation (<1s requirement)
- **Throughput**: Handles multiple symbols concurrently
- **Memory**: Efficient stream processing with minimal buffering
- **CPU**: Optimized calculations using numpy vectorization
- **Monitoring**: Real-time performance metrics via Prometheus

## Architecture

The runtime engine operates as an asynchronous service:

1. **Market Data Ingestion**: Connects to Binance WebSocket streams
2. **Signal Processing**: Analyzes 1-minute K-line data in real-time
3. **Probability Calculation**: Generates directional predictions
4. **Signal Distribution**: Broadcasts signals via WebSocket to dashboard
5. **Data Storage**: Persists market data to InfluxDB, signals to Redis

## Monitoring

- **Health Checks**: Built-in health monitoring endpoints
- **Metrics**: Prometheus metrics for signal generation performance
- **Logging**: Structured JSON logging for observability
- **Alerts**: System alerts for connection failures and errors
