"use client";

import { useEffect, useMemo, useState } from 'react';
import Dashboard from '@/components/layout/Dashboard';
import SignalList, { TradingSignal as UiSignal } from '@/components/signals/SignalList';

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
    <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Signals</h2>
        <p className="text-sm text-gray-500">Generate and view latest trading signals</p>
      </div>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          className="input w-44"
          placeholder="Symbol (e.g., BTCUSDT)"
        />
        <button onClick={generateSignal} className="btn btn-primary" disabled={loading}>
          {loading ? 'Working…' : 'Generate Signal'}
        </button>
        <button onClick={fetchSignals} className="btn btn-secondary" disabled={loading}>
          Refresh
        </button>
      </div>
    </div>
  ), [symbol, loading]);

  return (
    <Dashboard currentPage="Signals">
      <div className="space-y-6">
        {header}
        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}
        <SignalList signals={signals} />
      </div>
    </Dashboard>
  );
}

