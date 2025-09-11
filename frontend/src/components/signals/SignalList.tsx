'use client';

import { motion } from 'framer-motion';
import { Card } from '@/components/ui';
import { staggerContainer, staggerItem } from '@/utils/animations';
import { clsx } from 'clsx';
import { SignalCard, TradingSignal } from './SignalCard';

/**
 * SignalList
 * Presentational component that renders a list of trading signals.
 * Uses project's design system components and animations for consistency.
 */

export interface SignalListProps {
  signals: TradingSignal[];
  className?: string;
  variant?: 'card' | 'list';
  loading?: boolean;
}

const confidenceColors: Record<'LOW' | 'MEDIUM' | 'HIGH', string> = {
  LOW: 'badge-warning',
  MEDIUM: 'badge-secondary',
  HIGH: 'badge-success',
};

const directionColors: Record<'UP' | 'DOWN', string> = {
  UP: 'text-success-600',
  DOWN: 'text-danger-600',
};

const directionIcons: Record<'UP' | 'DOWN', string> = {
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

export function SignalList({ 
  signals, 
  className, 
  variant = 'list',
  loading = false 
}: SignalListProps) {
  if (loading) {
    return (
      <div className={clsx('w-full', className)}>
        <Card className="p-6">
          <div className="flex items-center justify-center">
            <div className="loading-spinner" />
            <span className="ml-2 text-muted-foreground">加载信号中...</span>
          </div>
        </Card>
      </div>
    );
  }

  if (signals.length === 0) {
    return (
      <div className={clsx('w-full', className)}>
        <Card className="p-8">
          <div className="text-center">
            <div className="mb-4 text-muted-foreground">
              <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-foreground mb-2">暂无信号</h3>
            <p className="text-muted-foreground">当前没有可显示的交易信号，请稍后再试或生成新信号。</p>
          </div>
        </Card>
      </div>
    );
  }

  if (variant === 'card') {
    return (
      <motion.div 
        className={clsx('w-full grid gap-4 md:grid-cols-2 lg:grid-cols-3', className)}
        variants={staggerContainer}
        initial="initial"
        animate="animate"
      >
        {signals.map((signal) => (
          <motion.div key={signal.id} variants={staggerItem}>
            <SignalCard signal={signal} interactive />
          </motion.div>
        ))}
      </motion.div>
    );
  }

  return (
    <div className={clsx('w-full', className)}>
      <Card className="overflow-hidden">
        <motion.div 
          variants={staggerContainer}
          initial="initial"
          animate="animate"
        >
          <div className="divide-y divide-border">
            {signals.map((s: TradingSignal) => (
              <motion.div key={s.id} variants={staggerItem}>
                <div className="p-4 sm:p-5 hover:bg-muted/50 transition-colors">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className={clsx(
                          'flex items-center gap-1 text-sm font-medium',
                          directionColors[s.direction]
                        )}
                        aria-label={`Direction ${s.direction}`}
                        title={`Direction ${s.direction}`}
                      >
                        <span className="text-base">{directionIcons[s.direction]}</span>
                        {s.direction}
                      </div>
                      <div className="text-sm font-semibold text-foreground" title="Symbol">
                        {s.symbol}
                      </div>
                      <span
                        className={clsx('badge', confidenceColors[s.confidence_level])}
                        title="Confidence Level"
                      >
                        {s.confidence_level}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
                      <div className="flex items-center gap-1" title="Predicted Probability">
                        <span className="text-muted-foreground">概率:</span>
                        <span className="font-medium text-foreground">{formatPercent(s.predicted_probability)}</span>
                      </div>
                      <div className="flex items-center gap-1" title="Timestamp">
                        <span className="text-muted-foreground">时间:</span>
                        <time className="font-medium text-foreground" dateTime={s.timestamp}>
                          {formatDate(s.timestamp)}
                        </time>
                      </div>
                      <div className="flex items-center gap-1" title="Expiry">
                        <span className="text-muted-foreground">到期:</span>
                        <time className="font-medium text-foreground" dateTime={s.expiry_time}>
                          {formatDate(s.expiry_time)}
                        </time>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </Card>
    </div>
  );
}

export default SignalList;