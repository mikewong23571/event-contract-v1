import Link from 'next/link';
import Dashboard from '@/components/layout/Dashboard';

export default function HomePage() {
  return (
    <Dashboard currentPage="Home">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Event Contract Trading System</h1>
        <p className="text-gray-600">Probability-based trading signals for Binance event contracts</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="card flex flex-col">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Trading Signals</h3>
          <p className="text-gray-600 text-sm mb-4">Real-time probability-based signals with risk assessment</p>
          <div className="mt-auto">
            <Link href="/signals" className="btn btn-primary w-full">View Signals</Link>
          </div>
        </div>

        <div className="card flex flex-col">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Market Data</h3>
          <p className="text-gray-600 text-sm mb-4">Live K-line data and multi-timeframe indicators</p>
          <div className="mt-auto">
            <Link href="/market-data" className="btn btn-primary w-full">Open Market Data</Link>
          </div>
        </div>

        <div className="card flex flex-col">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Backtesting</h3>
          <p className="text-gray-600 text-sm mb-4">Historical simulation and performance analysis</p>
          <div className="mt-auto">
            <Link href="/backtesting" className="btn btn-primary w-full">Run Backtest</Link>
          </div>
        </div>
      </div>

      <div className="mt-10 grid gap-6 md:grid-cols-2">
        <div className="card">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span className="text-sm text-gray-700">Backend API</span>
            </div>
            <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="text-sm text-blue-600 hover:underline">Docs</a>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span className="text-sm text-gray-700">WebSocket</span>
            </div>
            <span className="text-sm text-gray-500">Connected</span>
          </div>
        </div>
      </div>
    </Dashboard>
  );
}
