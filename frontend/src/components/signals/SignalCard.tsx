'use client';

import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui';
import { fadeIn } from '@/utils/animations';
import { clsx } from 'clsx';

/**
 * SignalCard
 * Presentational component that renders a single trading signal in a card layout.
 * Uses project's design system components for consistency.
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
  interactive?: boolean;
}

const confidenceColors: Record<ConfidenceLevel, string> = {
  LOW: 'badge-warning',
  MEDIUM: 'badge-secondary',
  HIGH: 'badge-success',
};

const directionColors: Record<Direction, string> = {
  UP: 'text-success-600',
  DOWN: 'text-danger-600',
};

const directionIcons: Record<Direction, string> = {
  UP: '↗',
  DOWN: '↘',
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

export function SignalCard({ signal, className, interactive = false }: SignalCardProps) {
  const s = signal;

  return (
    <motion.div
      variants={fadeIn}
      initial="initial"
      animate="animate"
      className={className}
    >
      <Card 
        variant="default" 
        hover={interactive}
        interactive={interactive}
        className="transition-all duration-200"
        aria-label={`Trading signal for ${s.symbol}`}
      >
        <CardContent className="p-4 sm:p-5">
          <div className="flex items-start justify-between gap-4 mb-4">
            <div className="flex items-center gap-3">
              <div
                className={clsx(
                  'flex items-center gap-1 text-sm font-medium',
                  directionColors[s.direction]
                )}
                aria-label={`Direction ${s.direction}`}
                title={`Direction ${s.direction}`}
              >
                <span className="text-lg">{directionIcons[s.direction]}</span>
                {s.direction}
              </div>
              <h3 className="text-base font-semibold text-foreground" title="Symbol">
                {s.symbol}
              </h3>
              <span
                className={clsx('badge', confidenceColors[s.confidence_level])}
                title="Confidence Level"
              >
                {s.confidence_level}
              </span>
            </div>

            <div className="text-xs text-muted-foreground" title="Signal ID">
              #{s.id.slice(-8)}
            </div>
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="flex items-center gap-2" title="Predicted Probability">
              <span className="text-muted-foreground text-sm">概率</span>
              <span className="font-medium text-foreground">{formatPercent(s.predicted_probability)}</span>
            </div>
            <div className="flex items-center gap-2" title="Timestamp">
              <span className="text-muted-foreground text-sm">时间</span>
              <time className="font-medium text-foreground text-sm" dateTime={s.timestamp}>
                {formatDate(s.timestamp)}
              </time>
            </div>
            <div className="flex items-center gap-2" title="Expiry">
              <span className="text-muted-foreground text-sm">到期</span>
              <time className="font-medium text-foreground text-sm" dateTime={s.expiry_time}>
                {formatDate(s.expiry_time)}
              </time>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export default SignalCard;