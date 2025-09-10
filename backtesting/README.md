# Event Contract Trading System - Backtesting Engine

High-performance backtesting engine for validating trading strategies against historical market data.

## Tech Stack

- **Python**: 3.11+
- **Data Processing**: pandas 2.1.4, NumPy 1.25.2
- **Statistical Analysis**: SciPy, statsmodels, scikit-learn
- **Visualization**: matplotlib, seaborn, plotly
- **Performance**: numba (JIT compilation), bottleneck
- **Storage**: HDF5 (h5py), Parquet (pyarrow)
- **Testing**: pytest with coverage

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Development dependencies
pip install -e ".[dev]"
```

## Usage

```bash
# Run backtesting via CLI
backtest --strategy=signal_based --symbol=BTCUSDT --start=2024-01-01 --end=2024-12-31

# Run specific backtest
python -m src.cli.backtest_cli --config=configs/strategy.yaml

# Generate performance report
python -m src.analyzers.performance_analyzer --results=results/backtest_001.h5
```

## Features

- **Historical Data Loading**: Efficient loading and preprocessing of market data
- **Strategy Simulation**: Event contract strategy execution simulation
- **Performance Analysis**: Comprehensive performance metrics and reporting
- **Risk Metrics**: Drawdown, Sharpe ratio, win rate, expectancy calculations
- **Visualization**: Interactive charts and performance plots
- **Parallel Processing**: Multi-core backtesting for large datasets
- **Result Storage**: Efficient storage in HDF5 and Parquet formats

## Project Structure

```
backtesting/
├── src/
│   ├── models/          # Data models (BacktestResult, BacktestTrade)
│   ├── loaders/         # Data loading utilities
│   ├── simulators/      # Strategy simulation engine
│   ├── analyzers/       # Performance analysis tools
│   ├── generators/      # Report generation
│   ├── lib/             # Core backtesting library
│   ├── cli/             # Command-line interface
│   └── config/          # Configuration management
├── tests/
│   ├── integration/     # Integration tests
│   └── unit/           # Unit tests
├── data/               # Historical data storage
├── results/            # Backtesting results
└── configs/            # Strategy configurations
```

## Performance Considerations

- Uses numba for JIT compilation of critical loops
- Vectorized operations with pandas and numpy
- Efficient memory management for large datasets
- Parallel processing support for multiple symbols/periods
- Incremental result storage to handle long-running backtests

## Validation

All backtesting results include:
- Forward-looking bias detection
- Data snooping protection via walk-forward analysis
- Statistical significance testing
- Out-of-sample validation periods
- Monte Carlo simulation for confidence intervals