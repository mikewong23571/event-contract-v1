/* Using the automatic JSX runtime; no explicit React import required. */

/**
 * SignalCard
 * Presentational component that renders a single trading signal in a card layout.
 * Scope: Display-only. This component does not fetch data or manage WebSocket connections.
 *
 * Notes:
 * - Styling follows TailwindCSS conventions used in the project.
 * - Time values are displayed using the user's locale via toLocaleString().
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

export interface SignalCardProps {
  signal: TradingSignal;
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

export function SignalCard({ signal, className }: SignalCardProps) {
  const s = signal;

  return (
    <article
      className={[
        'rounded-lg border border-gray-200 bg-white p-4 shadow-sm sm:p-5',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      aria-label={`Trading signal for ${s.symbol}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className={`text-sm font-medium ${directionColors[s.direction]}`}
            aria-label={`Direction ${s.direction}`}
            title={`Direction ${s.direction}`}
          >
            {s.direction === 'UP' ? '↑ UP' : '↓ DOWN'}
          </div>
          <h3 className="text-base font-semibold text-gray-900" title="Symbol">
            {s.symbol}
          </h3>
          <span
            className={`inline-flex items-center rounded-md px-2 py-1 text-xs ring-1 ring-inset ${confidenceColors[s.confidence_level]}`}
            title="Confidence Level"
          >
            {s.confidence_level}
          </span>
        </div>

        <div className="text-xs text-gray-500" title="Signal ID">
          #{s.id}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="flex items-center gap-2" title="Predicted Probability">
          <span className="text-gray-500">Probability</span>
          <span className="font-medium text-gray-900">{formatPercent(s.predicted_probability)}</span>
        </div>
        <div className="flex items-center gap-2" title="Timestamp">
          <span className="text-gray-500">Time</span>
          <time className="font-medium text-gray-900" dateTime={s.timestamp}>
            {formatDate(s.timestamp)}
          </time>
        </div>
        <div className="flex items-center gap-2" title="Expiry">
          <span className="text-gray-500">Expires</span>
          <time className="font-medium text-gray-900" dateTime={s.expiry_time}>
            {formatDate(s.expiry_time)}
          </time>
        </div>
      </div>
    </article>
  );
}

export default SignalCard;