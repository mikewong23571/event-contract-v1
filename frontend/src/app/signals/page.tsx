"use client";

import { useEffect, useMemo, useState } from 'react';
import Dashboard from '@/components/layout/Dashboard';
import SignalList from '@/components/signals/SignalList';
import { TradingSignal as UiSignal } from '@/components/signals/SignalCard';
import { Input, Button } from '@/components/ui';

type ApiSignal = {
  timestamp: string;
  symbol: string;
  direction: 'UP' | 'DOWN';
  predicted_probability: number;
  confidence_level: 'LOW' | 'MEDIUM' | 'HIGH';
  expiry_time: string;
};

export default function SignalsPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [signals, setSignals] = useState<UiSignal[]>([]);
  const [symbol, setSymbol] = useState('BTCUSDT');

  const fetchSignals = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/signals?limit=20`, { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const items: ApiSignal[] = (data?.signals ?? []) as ApiSignal[];
      const mapped: UiSignal[] = items.map((s, idx) => ({
        id: `${s.symbol}-${s.timestamp}-${idx}`,
        ...s,
      }));
      setSignals(mapped);
    } catch (e: any) {
      setError(e.message ?? 'Failed to load signals');
    } finally {
      setLoading(false);
    }
  };

  const generateSignal = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/signals/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      // Refresh list after generation
      await fetchSignals();
    } catch (e: any) {
      setError(e.message ?? 'Failed to generate signal');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, []);

  const header = useMemo(() => (
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        <h2 className="text-2xl font-bold text-foreground mb-2">交易信号</h2>
        <p className="text-muted-foreground">生成和查看最新的交易信号</p>
      </div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          className="w-44"
          placeholder="交易对 (如: BTCUSDT)"
        />
        <div className="flex gap-2">
          <Button 
            onClick={generateSignal} 
            variant="primary" 
            disabled={loading}
          >
            {loading ? '生成中...' : '生成信号'}
          </Button>
          <Button 
            onClick={fetchSignals} 
            variant="secondary" 
            disabled={loading}
          >
            刷新
          </Button>
        </div>
      </div>
    </div>
  ), [symbol, loading]);

  return (
    <Dashboard currentPage="Signals">
      <div className="space-y-6 p-6">
        {header}
        {error && (
          <div className="card border-danger-200 bg-danger-50 p-4">
            <div className="flex items-center gap-3">
              <svg className="h-5 w-5 text-danger-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div>
                <h4 className="text-sm font-medium text-danger-800">加载失败</h4>
                <p className="text-sm text-danger-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}
        <SignalList signals={signals} loading={loading} />
      </div>
    </Dashboard>
  );
}

