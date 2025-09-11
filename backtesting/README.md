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

## Installation (uv)

```bash
# Install dependencies (uv)
uv sync

# Include dev extras (tests, linters, etc.)
uv sync --extra dev
```

## Usage

```bash
# Run backtesting via CLI
backtest --strategy=signal_based --symbol=BTCUSDT --start=2024-01-01 --end=2024-12-31

# Run specific backtest
uv run -m src.cli.backtest_cli --config=configs/strategy.yaml

# Generate performance report
uv run -m src.analyzers.performance_analyzer --results=results/backtest_001.h5
```

## Repo Workflow (uv + Make)

- 推荐使用仓库根目录的 Make 命令统一操作：
  - `make dev` 启动基础设施与所有应用服务（通过 uvx honcho + Procfile.dev）
  - `make test` 统一运行测试
  - `make format` / `make lint` / `make type-check` 执行代码质量工具
  - 所有 Python 工具均通过 `uv run` 运行，无需全局安装

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
