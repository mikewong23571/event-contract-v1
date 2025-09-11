import { render, screen } from '@testing-library/react';
import { BacktestResults, BacktestResult } from '../../src/components/backtesting/BacktestResults';

function makeResult(): BacktestResult {
  const now = new Date();
  const start = new Date(now.getTime() - 30 * 24 * 3600 * 1000);
  return {
    id: 'br-1',
    name: 'Sample Backtest',
    description: 'Test backtest rendering',
    metrics: {
      total_return: 0.15,
      annualized_return: 0.20,
      max_drawdown: 0.10,
      sharpe_ratio: 1.25,
      win_rate: 0.55,
      total_trades: 42,
      winning_trades: 23,
      losing_trades: 19,
      avg_win: 120.5,
      avg_loss: -80.25,
      profit_factor: 1.6,
      start_date: start.toISOString(),
      end_date: now.toISOString(),
      initial_capital: 10000,
      final_capital: 11500,
    },
    trades: [],
    portfolio_values: [
      { date: start.toISOString(), value: 10000, return_pct: 0 },
      { date: now.toISOString(), value: 11500, return_pct: 0.15 },
    ],
    created_at: now.toISOString(),
  };
}

describe('BacktestResults', () => {
  it('renders key metrics and charts container', () => {
    const result = makeResult();
    render(<BacktestResults result={result} />);

    expect(screen.getByText('Sample Backtest')).toBeInTheDocument();
    expect(screen.getByText('Total Return')).toBeInTheDocument();
    expect(screen.getByText('Sharpe Ratio')).toBeInTheDocument();
  });
});

