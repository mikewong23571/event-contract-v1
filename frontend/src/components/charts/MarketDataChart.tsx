/* Using the automatic JSX runtime; no explicit React import required. */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

/**
 * MarketDataChart
 * Real-time market data visualization component using Recharts library.
 * Displays price movements over time with responsive design.
 *
 * Features:
 * - Responsive chart that adapts to container size
 * - Real-time price data visualization
 * - Customizable styling and time ranges
 * - Interactive tooltips showing price and timestamp
 */

export interface MarketDataPoint {
  timestamp: string; // ISO 8601
  price: number;
  volume?: number;
  symbol: string;
}

export interface MarketDataChartProps {
  data: MarketDataPoint[];
  symbol: string;
  height?: number;
  className?: string;
  showVolume?: boolean;
}

function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return timestamp;
    return date.toLocaleTimeString();
  } catch {
    return timestamp;
  }
}

function formatPrice(price: number): string {
  return price.toFixed(4);
}

export function MarketDataChart({ 
  data, 
  symbol, 
  height = 300, 
  className,
  showVolume = false 
}: MarketDataChartProps) {
  const chartData = data.map(point => ({
    ...point,
    formattedTime: formatTimestamp(point.timestamp),
    formattedPrice: formatPrice(point.price)
  }));

  return (
    <div 
      className={['w-full rounded-lg border border-gray-200 bg-white p-4', className]
        .filter(Boolean)
        .join(' ')}
    >
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">{symbol} Price Chart</h3>
        <div className="text-sm text-gray-500">
          {data.length > 0 && (
            <span>Latest: ${formatPrice(data[data.length - 1]?.price || 0)}</span>
          )}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={chartData}
          margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 20,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
          <XAxis 
            dataKey="formattedTime"
            stroke="#6b7280"
            fontSize={12}
            tickLine={false}
          />
          <YAxis 
            stroke="#6b7280"
            fontSize={12}
            tickLine={false}
            domain={['dataMin - 0.001', 'dataMax + 0.001']}
            tickFormatter={formatPrice}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '12px'
            }}
            labelStyle={{ color: '#374151' }}
            formatter={(value: number, name: string) => [
              `$${formatPrice(value)}`,
              name === 'price' ? 'Price' : name
            ]}
            labelFormatter={(label: string) => `Time: ${label}`}
          />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#3b82f6' }}
          />
          {showVolume && (
            <Line 
              type="monotone" 
              dataKey="volume" 
              stroke="#10b981"
              strokeWidth={1}
              dot={false}
              yAxisId="volume"
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      {data.length === 0 && (
        <div className="flex items-center justify-center" style={{ height }}>
          <p className="text-sm text-gray-500">No market data available</p>
        </div>
      )}
    </div>
  );
}

export default MarketDataChart;