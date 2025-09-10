export default function HomePage() {
  return (
    <main className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Event Contract Trading System
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Probability-based trading signals for Binance event contracts
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Trading Signals
            </h3>
            <p className="text-gray-600 text-sm">
              Real-time probability-based signals with risk assessment
            </p>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Market Data
            </h3>
            <p className="text-gray-600 text-sm">
              Live 1-minute K-line data and multi-timeframe indicators
            </p>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Backtesting
            </h3>
            <p className="text-gray-600 text-sm">
              Historical simulation and performance analysis
            </p>
          </div>
        </div>

        <div className="mt-12 text-center">
          <div className="inline-flex items-center px-4 py-2 rounded-lg bg-primary-50 text-primary-700">
            <div className="w-2 h-2 bg-primary-500 rounded-full mr-2"></div>
            System Status: Ready
          </div>
        </div>
      </div>
    </main>
  );
}