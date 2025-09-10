/* Using the automatic JSX runtime; no explicit React import required. */

/**
 * SignalList
 * Presentational component that renders a list of trading signals.
 * Scope: Display-only. This component does not fetch data or manage WebSocket connections.
 */

export type Direction = 'UP' | 'DOWN';
export type ConfidenceLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface TradingSignal {
  id: string;
  timestamp: string; // ISO 8601
  symbol: string;
  direction: Direction;
  predicted_probability: number; // 0.0 - 1.0
  confidence_level: ConfidenceLevel;
  expiry_time: string; // ISO 8601
}

export interface SignalListProps {
  signals: TradingSignal[];
  className?: string;
}

const confidenceColors: Record<ConfidenceLevel, string> = {
  LOW: 'bg-yellow-100 text-yellow-800 ring-yellow-600/20',
  MEDIUM: 'bg-blue-100 text-blue-800 ring-blue-600/20',
  HIGH: 'bg-green-100 text-green-800 ring-green-600/20',
};

const directionColors: Record<Direction, string> = {
  UP: 'text-green-600',
  DOWN: 'text-red-600',
};

function formatPercent(n: number): string {
  const pct = Math.round(n * 1000) / 10; // 1 decimal place
  return `${pct}%`;
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString();
  } catch {
    return iso;
  }
}

export function SignalList({ signals, className }: SignalListProps) {
  return (
    <div className={['w-full', className].filter(Boolean).join(' ')}>
      <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
        {signals.map((s: TradingSignal) => (
          <li key={s.id} className="p-4 sm:p-5">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <div
                  className={`text-sm font-medium ${directionColors[s.direction]}`}
                  aria-label={`Direction ${s.direction}`}
                  title={`Direction ${s.direction}`}
                >
                  {s.direction === 'UP' ? '↑ UP' : '↓ DOWN'}
                </div>
                <div className="text-sm font-semibold text-gray-900" title="Symbol">
                  {s.symbol}
                </div>
                <span
                  className={`inline-flex items-center rounded-md px-2 py-1 text-xs ring-1 ring-inset ${confidenceColors[s.confidence_level]}`}
                  title="Confidence Level"
                >
                  {s.confidence_level}
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
                <div className="flex items-center gap-1" title="Predicted Probability">
                  <span className="text-gray-500">Prob:</span>
                  <span className="font-medium text-gray-900">{formatPercent(s.predicted_probability)}</span>
                </div>
                <div className="flex items-center gap-1" title="Timestamp">
                  <span className="text-gray-500">Time:</span>
                  <time className="font-medium text-gray-900" dateTime={s.timestamp}>
                    {formatDate(s.timestamp)}
                  </time>
                </div>
                <div className="flex items-center gap-1" title="Expiry">
                  <span className="text-gray-500">Expires:</span>
                  <time className="font-medium text-gray-900" dateTime={s.expiry_time}>
                    {formatDate(s.expiry_time)}
                  </time>
                </div>
              </div>
            </div>
          </li>
        ))}
        {signals.length === 0 && (
          <li className="p-6 text-center text-sm text-gray-500">No signals to display.</li>
        )}
      </ul>
    </div>
  );
}

export default SignalList;