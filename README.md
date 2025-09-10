# Event Contract Trading System

A comprehensive trading system for Binance event contracts featuring probability-based signals, risk management, backtesting, and multi-channel notifications.

## 🏗️ Architecture

The system consists of 4 main components:

- **Backend**: FastAPI-based API server with real-time WebSocket support
- **Frontend**: Next.js dashboard with TailwindCSS for trading visualization
- **Backtesting Engine**: High-performance backtesting with pandas/numpy
- **Runtime Engine**: Real-time signal detection with WebSocket streaming
- **Notifications**: Multi-channel alerts (Telegram, Feishu, Email)

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18.0 or higher  
- **Docker**: 20.10+ and Docker Compose 2.0+
- **Binance API**: Testnet account for development

### 1. Clone and Setup

```bash
git clone <repository-url>
cd event-contract-v1

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys and settings
```

### 2. Start Infrastructure Services

```bash
# Start PostgreSQL, InfluxDB, Redis
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 3. Install Dependencies

```bash
# Install Python dependencies for all components
cd backend && pip install -r requirements.txt
cd ../backtesting && pip install -r requirements.txt
cd ../runtime && pip install -r requirements.txt
cd ../notifications && pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend && npm install
```

### 4. Start Development Services

```bash
# Terminal 1: Backend API
cd backend && python -m src.main

# Terminal 2: Frontend Dashboard
cd frontend && npm run dev

# Terminal 3: Runtime Engine
cd runtime && python -m src.main

# Terminal 4: Notifications Service
cd notifications && python -m src.main
```

### 5. Access the System

- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **pgAdmin**: http://localhost:5050 (admin/admin)
- **Redis Commander**: http://localhost:8081 (admin/admin)

## 📁 Project Structure

```
event-contract-v1/
├── backend/              # FastAPI backend service
├── frontend/             # Next.js dashboard
├── backtesting/          # Backtesting engine
├── runtime/              # Real-time signal detection
├── notifications/        # Multi-channel notifications
├── specs/                # Feature specifications and plans
├── memory/               # Project constitution and guidelines
├── templates/            # Development templates
├── scripts/              # Utility scripts
├── docker-compose.yml    # Infrastructure services
├── .env.example          # Environment configuration template
└── Makefile              # Development commands
```

## 🛠️ Development

### Code Quality

The project uses unified code quality tools across all components:

```bash
# Format all code
make format

# Lint all code  
make lint

# Type checking
make type-check

# Run all tests
make test

# Full CI pipeline
make ci
```

### Database Management

```bash
# Reset all data
docker-compose down -v
docker-compose up -d

# View logs
docker-compose logs -f postgres
docker-compose logs -f influxdb
docker-compose logs -f redis
```

### Component Development

Each component has its own development setup:

```bash
# Backend development
cd backend
pip install -e ".[dev]"
python -m pytest
uvicorn src.main:app --reload

# Frontend development  
cd frontend
npm run dev
npm run build
npm run lint

# Backtesting
cd backtesting
python -m src.cli.backtest_cli --help
pytest tests/

# Runtime engine
cd runtime
python -m src.main
pytest tests/

# Notifications
cd notifications
celery -A src.main:celery_app worker --loglevel=info
pytest tests/
```

## 🧪 Testing

The project follows TDD (Test-Driven Development) principles:

- **Contract Tests**: API endpoint validation
- **Integration Tests**: Component interaction testing
- **Unit Tests**: Individual function testing
- **End-to-End Tests**: Full workflow validation

```bash
# Run specific test types
make test-contract
make test-integration  
make test-unit
make test-e2e
```

## 📊 Monitoring

### Health Checks

- Backend: http://localhost:8000/health
- Runtime: Check logs for service status
- Database: http://localhost:5050 (pgAdmin)
- Cache: http://localhost:8081 (Redis Commander)

### Metrics

Prometheus metrics available on port 9090:
- Signal generation latency
- API request rates
- Database connection health
- Notification delivery rates

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db
INFLUXDB_URL=http://localhost:8086
REDIS_URL=redis://localhost:6379/0

# Binance API
BINANCE_API_KEY=your_api_key
BINANCE_SECRET_KEY=your_secret_key
BINANCE_TESTNET=true

# Notifications
TELEGRAM_BOT_TOKEN=your_bot_token
FEISHU_WEBHOOK_URL=your_webhook_url
```

### Trading Parameters

```bash
# Signal detection
SIGNAL_INTERVAL=1.0
MIN_CONFIDENCE=0.6
TRADING_SYMBOLS=BTCUSDT,ETHUSDT

# Risk management  
MAX_POSITION_SIZE=1000
MAX_DAILY_TRADES=50
```

## 📈 Features

- **Real-time Signals**: Probability-based trading signals with <1s latency
- **Risk Management**: Configurable position limits and exposure controls
- **Backtesting**: Historical validation with statistical analysis
- **Multi-channel Alerts**: Telegram, Feishu, Email notifications
- **Interactive Dashboard**: Real-time charts and signal visualization
- **Performance Analytics**: Comprehensive trading metrics and reports

## 🚀 Deployment

### Production Setup

1. **Environment**: Update `.env` for production settings
2. **Database**: Configure production PostgreSQL/InfluxDB instances  
3. **Security**: Generate secure JWT keys and API credentials
4. **Monitoring**: Set up Prometheus/Grafana dashboards
5. **Scaling**: Configure load balancers and multiple service instances

### Docker Production

```bash
# Production build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale backend=3 --scale runtime=2
```

## 🤝 Contributing

1. Follow the constitutional requirements in `/memory/constitution.md`
2. All features start with specifications in `/specs/`
3. Implement using TDD with contract tests first
4. Ensure code quality with `make ci` before submitting
5. Update documentation for new features

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading cryptocurrencies involves significant risk. The authors are not responsible for any financial losses incurred through the use of this software.