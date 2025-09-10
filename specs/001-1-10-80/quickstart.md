# Quickstart: Event Contract Trading System

**Feature**: Event Contract Trading System  
**Version**: 0.1.0  
**Date**: 2025-09-10

## Overview
This quickstart guide walks you through setting up and using the Event Contract Trading System for Binance binary prediction contracts. The system provides probability-based trading signals with risk management to help make informed manual trading decisions.

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or macOS
- **Python**: 3.11 or higher
- **Docker**: 20.10+ and Docker Compose 2.0+
- **Node.js**: 18.0+ (for dashboard frontend)
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: 100GB+ free space for market data

### External Dependencies
- **Binance API Account**: Required for market data access
- **PostgreSQL**: 14+ (can run via Docker)
- **InfluxDB**: 2.7+ for time-series data
- **Redis**: 7.0+ for caching and pub/sub

## Quick Setup (Docker)

### 1. Clone and Configure
```bash
git clone <repository-url>
cd event-contract-v1

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your Binance API credentials and other settings
```

### 2. Start All Services
```bash
# Start infrastructure services (databases, cache)
docker-compose up -d postgres influxdb redis

# Wait for services to be ready (about 30 seconds)
./scripts/wait-for-services.sh

# Start trading system components
docker-compose up -d dashboard-backend dashboard-frontend runtime-engine

# Start backtesting service (optional, for historical analysis)
docker-compose up -d backtesting-engine
```

### 3. Verify Installation
```bash
# Check all services are running
docker-compose ps

# Health check
curl http://localhost:8000/api/v1/health

# Expected response:
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "market_data_feed": "ok", 
    "signal_generation": "ok"
  },
  "timestamp": "2025-09-10T10:30:00Z"
}
```

## First Run Experience

### 1. Access the Dashboard
Open your browser and navigate to: **http://localhost:3000**

You'll see the Event Contract Trading Dashboard with:
- **Market Data**: Real-time price charts for major pairs
- **Signal Feed**: Currently empty (no signals until configured)
- **Risk Management**: Default safe parameters
- **Performance**: No data yet

### 2. Configure Risk Parameters
Click on **Settings** → **Risk Management**:
```json
{
  "max_bet_size": "50.00",
  "max_daily_bets": 5,
  "max_parallel_positions": 2,
  "min_probability_edge": "0.05",
  "frequency_limit_minutes": 15,
  "max_daily_loss": "200.00"
}
```

**Important**: Start with conservative settings while you evaluate the system.

### 3. Enable Market Data Feed
In the dashboard, go to **Data Sources** → **Binance**:
- Verify connection status shows "Connected"
- Select symbols to monitor (start with BTCUSDT)
- Confirm data is flowing in the **Market Data** tab

### 4. Wait for First Signal
The system needs to collect some market data before generating signals:
- **Minimum**: 30 minutes of data for basic indicators
- **Recommended**: 2+ hours for reliable signals
- **Optimal**: 24+ hours for best accuracy

## Core Usage Workflows

### 1. Manual Trading Workflow
```
1. Monitor dashboard for high-confidence signals
2. Signal appears with:
   - Direction: UP/DOWN
   - Probability: e.g., 67%
   - Edge: +8% over market odds
   - Expiry: Time remaining
3. Evaluate the signal context:
   - Check supporting indicators (RSI, MACD, etc.)
   - Review recent market conditions
   - Consider current risk exposure
4. Execute trade manually on Binance (if desired)
5. Track outcome in the performance tab
```

### 2. Backtesting Workflow
Test strategies before using them live:

**Via Dashboard**:
1. Go to **Backtesting** tab
2. Select date range (e.g., last 30 days)
3. Choose strategy: "ensemble_v1" (default)
4. Set execution mode: "CONTINUOUS" (recommended)
5. Click **Run Backtest**

**Via API**:
```bash
curl -X POST http://localhost:8000/api/v1/backtests \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_name": "ensemble_v1",
    "start_date": "2025-08-10",
    "end_date": "2025-09-09", 
    "symbol": "BTCUSDT",
    "execution_mode": "CONTINUOUS"
  }'
```

### 3. Performance Analysis
Track your system's effectiveness:
- **Win Rate**: Percentage of correct predictions
- **Profit/Loss**: Cumulative returns over time
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Worst losing streak
- **Edge Analysis**: How often the system finds profitable opportunities

## WebSocket Real-time Updates

### Connect to Signal Stream
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/signals/BTCUSDT');

ws.onmessage = function(event) {
  const signal = JSON.parse(event.data);
  console.log('New signal:', {
    direction: signal.data.direction,
    probability: signal.data.predicted_probability,
    edge: signal.data.probability_edge,
    expires: signal.data.expiry_time
  });
};
```

### Trading Alert Example
```javascript
const alertWs = new WebSocket('ws://localhost:8000/ws/alerts');

alertWs.onmessage = function(event) {
  const alert = JSON.parse(event.data);
  if (alert.data.alert_type === 'high_probability_signal') {
    // High-confidence trading opportunity
    showNotification(alert.data.message);
  }
};
```

## Common Commands

### Service Management
```bash
# Restart signal generation
docker-compose restart runtime-engine

# View logs for debugging
docker-compose logs -f dashboard-backend
docker-compose logs -f runtime-engine

# Update to latest version
git pull origin main
docker-compose pull
docker-compose up -d
```

### Data Management
```bash
# Clean old market data (keeps last 30 days)
curl -X DELETE http://localhost:8000/api/v1/admin/cleanup-data

# Export backtest results
curl http://localhost:8000/api/v1/backtests/{backtest_id}/export > backtest.json

# Import historical data
./scripts/import-historical-data.sh BTCUSDT 2025-08-01 2025-09-01
```

### Configuration Updates
```bash
# Update risk parameters via API
curl -X PUT http://localhost:8000/api/v1/risk-parameters \
  -H "Content-Type: application/json" \
  -d '{"max_bet_size": "100.00", "max_daily_bets": 8}'

# Reload strategy configuration
curl -X POST http://localhost:8000/api/v1/admin/reload-strategies
```

## Testing Your Setup

### 1. Signal Generation Test
Force a signal for testing:
```bash
curl -X POST http://localhost:8000/api/v1/signals \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "force_calculation": true}'
```

### 2. Risk Management Test
Try to exceed limits:
```bash
# This should be rejected due to risk limits
for i in {1..20}; do
  curl -X POST http://localhost:8000/api/v1/signals \
    -d '{"symbol": "BTCUSDT"}' &
done
```

### 3. Performance Test
```bash
# Run quick backtest
curl -X POST http://localhost:8000/api/v1/backtests \
  -d '{
    "strategy_name": "ensemble_v1",
    "start_date": "2025-09-01",
    "end_date": "2025-09-09",
    "symbol": "BTCUSDT"
  }'
```

## Understanding Signals

### Signal Components
- **Direction**: UP (price will be higher) or DOWN (price will be lower) in 10 minutes
- **Probability**: Model's confidence (0.0 to 1.0)
- **Edge**: Advantage over Binance's implied probability
- **Confidence Level**: LOW (<60%), MEDIUM (60-70%), HIGH (70%+)

### When to Trade
**Good conditions**:
- High confidence (70%+) with significant edge (5%+)
- Supporting technical indicators align
- Market conditions are stable
- Within your risk limits

**Avoid trading when**:
- Low edge (<3%) even with high probability
- Conflicting technical signals
- Already at risk limits
- Market is highly volatile or news-driven

## Performance Expectations

### Realistic Goals
- **Win Rate**: Target 55-65% (above breakeven ~55.6%)
- **Frequency**: 2-5 signals per day (conservative approach)
- **Edge**: Look for 3%+ advantage over implied odds
- **Risk**: Never risk more than 2-5% of account per trade

### Red Flags
Stop using if you see:
- Win rate consistently below 50%
- Large drawdowns (>20% of account)
- System errors or missed signals
- Correlation with your emotions rather than probability

## Troubleshooting

### Common Issues

**No Signals Generated**:
- Check market data feed is connected
- Verify sufficient historical data (24+ hours)
- Ensure risk parameters allow signals
- Check system logs for errors

**Poor Signal Performance**:
- May need more training data
- Market conditions might have changed
- Consider adjusting strategy parameters
- Run fresh backtest on recent data

**WebSocket Connection Issues**:
- Check firewall settings
- Verify browser/client supports WebSockets
- Try restarting the dashboard backend
- Check authentication tokens

### Support Resources
- **Logs**: Check `docker-compose logs` for detailed error messages
- **Health Endpoint**: Monitor `/api/v1/health` for system status
- **Metrics**: Review performance data for trends
- **Configuration**: Verify all environment variables are set correctly

## Next Steps

### 1. Paper Trading Period
- Run the system for 1-2 weeks without real money
- Track all signals and outcomes
- Fine-tune risk parameters based on performance

### 2. Strategy Customization
- Experiment with different probability thresholds
- Adjust technical indicator weights
- Test various execution modes in backtesting

### 3. Advanced Features
- Set up notification integrations (Telegram, email)
- Configure multiple symbol monitoring
- Implement custom risk rules
- Export data for external analysis

### 4. Production Considerations
- Set up monitoring and alerting
- Implement backup strategies
- Plan for system maintenance windows
- Consider redundancy for critical components

## Security Notes
- Never commit API keys to version control
- Use strong passwords for all services
- Keep the system updated with security patches
- Monitor access logs for suspicious activity
- Consider running on a dedicated server/VPS

---

**Remember**: This system is designed to assist with trading decisions, not replace human judgment. Always practice proper risk management and never trade more than you can afford to lose.