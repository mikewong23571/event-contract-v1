"use client";

import { useCallback, useEffect, useMemo, useState } from 'react';
import Dashboard from '@/components/layout/Dashboard';
import MarketDataChart from '@/components/charts/MarketDataChart';
import { Input, Button, Card } from '@/components/ui';

type Interval = '1m' | '5m' | '15m' | '1h';

type ApiMarketPoint = {
  timestamp: string;
  open_price: string;
  high_price: string;
  low_price: string;
  close_price: string;
  volume: string;
};

export default function MarketDataPage() {
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [interval, setInterval] = useState<Interval>('1m');
  const [limit, setLimit] = useState(100);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [points, setPoints] = useState<{ timestamp: string; price: number; symbol: string }[]>([]);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/market-data/${encodeURIComponent(symbol)}?interval=${interval}&limit=${limit}`, { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const items: ApiMarketPoint[] = data?.data ?? [];
      const mapped = items.map((d) => ({
        timestamp: d.timestamp,
        price: Number(d.close_price),
        symbol,
      }));
      setPoints(mapped.reverse());
    } catch (e: any) {
      setError(e.message ?? 'Failed to load market data');
    } finally {
      setLoading(false);
    }
  }, [symbol, interval, limit]);

  useEffect(() => { loadData(); }, [loadData]);

  const controls = useMemo(() => (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Market Data</h2>
        <p className="text-sm text-gray-500">Live K-line data via backend API</p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Input className="w-40" value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} />
        <select className="input w-28" value={interval} onChange={(e) => setInterval(e.target.value as Interval)}>
          <option value="1m">1m</option>
          <option value="5m">5m</option>
          <option value="15m">15m</option>
          <option value="1h">1h</option>
        </select>
        <select className="input w-28" value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
          <option value={50}>50</option>
          <option value={100}>100</option>
          <option value={200}>200</option>
          <option value={500}>500</option>
        </select>
        <Button variant="primary" onClick={loadData} disabled={loading}>{loading ? 'Loading…' : 'Refresh'}</Button>
      </div>
    </div>
  ), [symbol, interval, limit, loading, loadData]);

  return (
    <Dashboard currentPage="Market Data">
      <div className="space-y-6">
        {controls}
        {error && (
          <Card variant="outlined" className="border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</Card>
        )}
        <MarketDataChart data={points} symbol={symbol} height={360} />
      </div>
    </Dashboard>
  );
}

