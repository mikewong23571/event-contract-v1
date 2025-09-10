# Data Model: Event Contract Trading System

**Feature**: Event Contract Trading System  
**Date**: 2025-09-10  
**Phase**: Design Phase 1

## Core Entities

### 1. TradingSignal
**Purpose**: Represents a directional prediction with probability and metadata
```python
class TradingSignal:
    id: UUID
    timestamp: datetime
    symbol: str              # e.g., "BTCUSDT"
    direction: str           # "UP" or "DOWN"  
    predicted_probability: float  # 0.0 to 1.0
    confidence_level: str    # "LOW", "MEDIUM", "HIGH"
    expiry_time: datetime    # When the contract expires
    strategy_version: str    # Which model/strategy generated this
    technical_indicators: dict  # Supporting indicator values
    created_at: datetime
    expires_at: datetime     # Signal relevance expiry
```

**Validation Rules**:
- predicted_probability must be between 0.0 and 1.0
- direction must be "UP" or "DOWN"
- expiry_time must be in the future
- confidence_level must match enum values

**State Transitions**:
- GENERATED → EXPIRED (time-based)
- GENERATED → EXECUTED (user action)

### 2. MarketData
**Purpose**: 1-minute candlestick data with volume information
```python
class MarketData:
    id: UUID
    symbol: str
    timestamp: datetime      # Start of the 1-minute period
    open_price: decimal
    high_price: decimal
    low_price: decimal
    close_price: decimal
    volume: decimal
    quote_volume: decimal    # Volume in quote asset
    trade_count: int
    source: str              # "binance_ws", "binance_rest"
    created_at: datetime
```

**Validation Rules**:
- All prices must be positive
- high_price >= max(open_price, close_price)
- low_price <= min(open_price, close_price)
- volume and quote_volume must be non-negative

### 3. EventContract
**Purpose**: Binary prediction contract details from Binance
```python
class EventContract:
    id: UUID
    contract_id: str         # Binance contract identifier
    symbol: str
    strike_price: decimal    # Price at contract creation
    expiry_time: datetime    # Contract settlement time
    payout_ratio: decimal    # e.g., 0.80 for 80% return
    implied_probability: decimal  # Calculated from payout ratio
    status: str              # "ACTIVE", "SETTLED", "CANCELLED"
    settlement_price: decimal  # Final price at expiry (if settled)
    created_at: datetime
    updated_at: datetime
```

**Validation Rules**:
- payout_ratio must be positive
- implied_probability = payout_ratio / (1 + payout_ratio)
- expiry_time must be future when status is "ACTIVE"

**State Transitions**:
- ACTIVE → SETTLED (at expiry_time)
- ACTIVE → CANCELLED (if contract cancelled)

### 4. RiskParameters
**Purpose**: User-configured risk management settings
```python
class RiskParameters:
    id: UUID
    user_id: str             # User identifier
    max_bet_size: decimal    # Maximum single bet amount
    max_daily_bets: int      # Maximum bets per day
    max_parallel_positions: int  # Maximum concurrent positions
    min_probability_edge: decimal  # Minimum advantage required
    frequency_limit_minutes: int  # Minimum time between bets
    max_daily_loss: decimal  # Daily loss limit
    created_at: datetime
    updated_at: datetime
```

**Validation Rules**:
- All numeric values must be positive
- min_probability_edge typically between 0.01 and 0.20

### 5. BacktestResult
**Purpose**: Historical simulation performance data
```python
class BacktestResult:
    id: UUID
    strategy_name: str
    start_date: datetime
    end_date: datetime
    total_signals: int
    successful_signals: int
    win_rate: decimal        # successful_signals / total_signals
    total_profit_loss: decimal
    max_drawdown: decimal
    sharpe_ratio: decimal
    parameters: dict         # Strategy configuration used
    execution_mode: str      # "FIRST_SIGNAL", "CONTINUOUS", "ENHANCED"
    created_at: datetime
```

**Validation Rules**:
- win_rate must be between 0.0 and 1.0
- total_signals must equal len(backtest_trades)
- successful_signals <= total_signals

### 6. BacktestTrade
**Purpose**: Individual simulated trade within a backtest
```python
class BacktestTrade:
    id: UUID
    backtest_result_id: UUID  # Foreign key
    signal_timestamp: datetime
    direction: str           # "UP" or "DOWN"
    entry_price: decimal
    exit_price: decimal
    bet_amount: decimal
    profit_loss: decimal     # Actual P&L from trade
    was_successful: bool     # True if prediction correct
    contract_duration_minutes: int  # Usually 10
    created_at: datetime
```

**Relationships**: 
- Many BacktestTrade belong to one BacktestResult

### 7. PerformanceMetrics
**Purpose**: Aggregated system performance statistics
```python
class PerformanceMetrics:
    id: UUID
    date: date               # Daily aggregation
    total_signals_generated: int
    total_signals_executed: int  # User actually traded
    daily_win_rate: decimal
    daily_profit_loss: decimal
    avg_signal_latency_ms: int
    system_uptime_percentage: decimal
    created_at: datetime
```

## Entity Relationships

### Primary Relationships
```
RiskParameters (1) ←→ (Many) TradingSignal
BacktestResult (1) ←→ (Many) BacktestTrade  
MarketData (Many) → TradingSignal (via timestamp correlation)
EventContract (1) ←→ (1) TradingSignal (optional, for actual trades)
```

### Derived Relationships
- TradingSignal references MarketData through symbol + timestamp
- PerformanceMetrics aggregates from TradingSignal daily
- BacktestResult uses historical MarketData for simulation

## Data Storage Strategy

### Time-Series Data (InfluxDB)
- **MarketData**: High-frequency, optimized for time-range queries
- **TradingSignal**: Medium-frequency, tagged by strategy and symbol
- **PerformanceMetrics**: Daily aggregation, long-term trends

### Relational Data (PostgreSQL)  
- **EventContract**: Structured contract data with ACID requirements
- **RiskParameters**: User configuration with referential integrity
- **BacktestResult/BacktestTrade**: Complex analytical queries

### File Storage
- **Backtest Reports**: Generated PDF/HTML reports
- **Model Artifacts**: Trained models, feature encoders
- **Configuration**: Strategy parameters, system config

## Data Access Patterns

### Real-time Patterns
- **Stream Processing**: MarketData → TradingSignal (sub-second)
- **Signal Distribution**: TradingSignal → WebSocket clients (immediate)
- **Risk Validation**: RiskParameters lookup on signal generation

### Analytical Patterns  
- **Performance Analysis**: Aggregate TradingSignal by time periods
- **Backtesting**: Batch process historical MarketData
- **Reporting**: Join BacktestResult with BacktestTrade for insights

### Caching Strategy
- **Recent MarketData**: Redis (last 24 hours)
- **Active RiskParameters**: Redis (per user)
- **Frequent Queries**: Query result caching (5-minute TTL)

## Data Validation & Integrity

### Input Validation
- JSON schema validation for API inputs  
- Database constraints for referential integrity
- Business rule validation in service layer

### Data Quality Checks
- Market data anomaly detection (price spikes, volume outliers)
- Signal probability bounds checking
- Risk parameter consistency validation

### Audit Trail
- All TradingSignal decisions logged with reasoning
- BacktestResult includes full parameter snapshots
- PerformanceMetrics provide system health monitoring

## Migration Strategy

### Schema Evolution
- Database migrations for schema changes
- Backward-compatible API versions
- Data transformation scripts for model updates

### Data Retention
- MarketData: 2 years rolling retention  
- TradingSignal: Permanent (small volume)
- BacktestResult: Permanent (analytical value)
- PerformanceMetrics: Permanent (trending analysis)