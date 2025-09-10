/* Using the automatic JSX runtime; no explicit React import required. */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

/**
 * BacktestResults
 * Component for displaying comprehensive backtesting results and performance metrics.
 * Shows portfolio performance, trade statistics, and visual charts.
 *
 * Features:
 * - Portfolio performance visualization
 * - Key performance metrics display
 * - Trade statistics and analysis
 * - Interactive charts and tables
 */

export interface BacktestTrade {
  id: string;
  entry_time: string; // ISO 8601
  exit_time: string; // ISO 8601
  symbol: string;
  direction: 'UP' | 'DOWN';
  entry_price: number;
  exit_price: number;
  quantity: number;
  pnl: number;
  pnl_percentage: number;
  result: 'WIN' | 'LOSS';
}

export interface BacktestMetrics {
  total_return: number; // Total return percentage
  annualized_return: number; // Annualized return percentage
  max_drawdown: number; // Maximum drawdown percentage
  sharpe_ratio: number;
  win_rate: number; // Win rate percentage
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  avg_win: number; // Average winning trade PnL
  avg_loss: number; // Average losing trade PnL
  profit_factor: number; // Gross profit / Gross loss
  start_date: string; // ISO 8601
  end_date: string; // ISO 8601
  initial_capital: number;
  final_capital: number;
}

export interface PortfolioValue {
  date: string; // ISO 8601
  value: number;
  return_pct: number; // Daily return percentage
}

export interface BacktestResult {
  id: string;
  name: string;
  description?: string;
  metrics: BacktestMetrics;
  trades: BacktestTrade[];
  portfolio_values: PortfolioValue[];
  created_at: string; // ISO 8601
}

export interface BacktestResultsProps {
  result: BacktestResult;
  className?: string;
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount);
}

function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

function formatDate(dateString: string): string {
  try {
    return new Date(dateString).toLocaleDateString();
  } catch {
    return dateString;
  }
}

export function BacktestResults({ result, className }: BacktestResultsProps) {
  const { metrics, trades, portfolio_values } = result;

  // Prepare portfolio chart data
  const portfolioChartData = portfolio_values.map(point => ({
    date: formatDate(point.date),
    value: point.value,
    return: point.return_pct * 100
  }));

  // Prepare monthly returns data
  const monthlyReturns = portfolio_values.reduce((acc, point) => {
    const month = new Date(point.date).toISOString().slice(0, 7); // YYYY-MM
    if (!acc[month]) {
      acc[month] = 0;
    }
    acc[month] += point.return_pct;
    return acc;
  }, {} as Record<string, number>);

  const monthlyReturnsData = Object.entries(monthlyReturns).map(([month, return_pct]) => ({
    month,
    return: return_pct * 100
  }));

  return (
    <div 
      className={['space-y-6', className].filter(Boolean).join(' ')}
    >
      {/* Header */}
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="text-xl font-semibold text-gray-900">{result.name}</h2>
        {result.description && (
          <p className="mt-1 text-sm text-gray-600">{result.description}</p>
        )}
        <div className="mt-2 text-sm text-gray-500">
          Period: {formatDate(metrics.start_date)} - {formatDate(metrics.end_date)}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <div className="text-sm font-medium text-gray-500">Total Return</div>
          <div className={`text-lg font-semibold ${metrics.total_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {formatPercentage(metrics.total_return)}
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <div className="text-sm font-medium text-gray-500">Sharpe Ratio</div>
          <div className="text-lg font-semibold text-gray-900">
            {metrics.sharpe_ratio.toFixed(2)}
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <div className="text-sm font-medium text-gray-500">Max Drawdown</div>
          <div className="text-lg font-semibold text-red-600">
            {formatPercentage(metrics.max_drawdown)}
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <div className="text-sm font-medium text-gray-500">Win Rate</div>
          <div className="text-lg font-semibold text-gray-900">
            {formatPercentage(metrics.win_rate)}
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <div className="text-sm font-medium text-gray-500">Total Trades</div>
          <div className="text-lg font-semibold text-gray-900">
            {metrics.total_trades.toLocaleString()}
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <div className="text-sm font-medium text-gray-500">Profit Factor</div>
          <div className="text-lg font-semibold text-gray-900">
            {metrics.profit_factor.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Portfolio Performance Chart */}
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Portfolio Performance</h3>
        <div style={{ height: '300px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={portfolioChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis 
                dataKey="date" 
                stroke="#6b7280" 
                fontSize={12}
                tickLine={false}
              />
              <YAxis 
                stroke="#6b7280" 
                fontSize={12}
                tickLine={false}
                tickFormatter={formatCurrency}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '12px'
                }}
                formatter={(value: number) => [formatCurrency(value), 'Portfolio Value']}
              />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Monthly Returns */}
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Monthly Returns</h3>
        <div style={{ height: '250px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={monthlyReturnsData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis 
                dataKey="month" 
                stroke="#6b7280" 
                fontSize={12}
                tickLine={false}
              />
              <YAxis 
                stroke="#6b7280" 
                fontSize={12}
                tickLine={false}
                tickFormatter={(value) => `${value.toFixed(1)}%`}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '12px'
                }}
                formatter={(value: number) => [`${value.toFixed(2)}%`, 'Monthly Return']}
              />
              <Bar 
                dataKey="return"
                fill="#3b82f6"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trade Statistics */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">Trade Statistics</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Winning Trades</span>
              <span className="text-sm font-medium text-green-600">
                {metrics.winning_trades} ({formatPercentage(metrics.winning_trades / metrics.total_trades)})
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Losing Trades</span>
              <span className="text-sm font-medium text-red-600">
                {metrics.losing_trades} ({formatPercentage(metrics.losing_trades / metrics.total_trades)})
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Average Win</span>
              <span className="text-sm font-medium text-green-600">
                {formatCurrency(metrics.avg_win)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Average Loss</span>
              <span className="text-sm font-medium text-red-600">
                {formatCurrency(metrics.avg_loss)}
              </span>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">Capital</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Initial Capital</span>
              <span className="text-sm font-medium text-gray-900">
                {formatCurrency(metrics.initial_capital)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Final Capital</span>
              <span className="text-sm font-medium text-gray-900">
                {formatCurrency(metrics.final_capital)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Net Profit</span>
              <span className={`text-sm font-medium ${(metrics.final_capital - metrics.initial_capital) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(metrics.final_capital - metrics.initial_capital)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-500">Annualized Return</span>
              <span className={`text-sm font-medium ${metrics.annualized_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatPercentage(metrics.annualized_return)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Trades */}
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Recent Trades (Last 10)</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Symbol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Direction
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Entry
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Exit
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  P&L
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Result
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {trades.slice(-10).reverse().map(trade => (
                <tr key={trade.id}>
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                    {trade.symbol}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      trade.direction === 'UP' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {trade.direction}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                    {formatCurrency(trade.entry_price)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                    {formatCurrency(trade.exit_price)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm">
                    <span className={trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                      {formatCurrency(trade.pnl)} ({formatPercentage(trade.pnl_percentage)})
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      trade.result === 'WIN' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {trade.result}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {trades.length === 0 && (
            <div className="py-8 text-center text-sm text-gray-500">
              No trades executed during this backtest.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default BacktestResults;