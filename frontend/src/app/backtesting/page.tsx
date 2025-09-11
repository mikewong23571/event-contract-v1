"use client";

import { useEffect, useState } from 'react';
import Dashboard from '@/components/layout/Dashboard';
import { LazyBacktestResultsWithFallback } from '@/components/lazy/LazyComponents';
import { useRenderTimeTracker, useApiTracker } from '@/stores/performanceStore';
import { Input, Button, Card } from '@/components/ui';

type CreateResponse = { backtest_id: string; status: string; created_at: string };
type GetResponse = { backtest_id: string; status: string; strategy_name: string; results?: { total_trades: number; win_rate: number; total_return: number }; summary?: string };

export default function BacktestingPage() {
  useRenderTimeTracker('BacktestingPage');
  const { trackApiCall } = useApiTracker();
  
  const [strategyName, setStrategyName] = useState('RSI Strategy');
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState('2024-12-31');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [backtestId, setBacktestId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);

  const createBacktest = async () => {
    setCreating(true);
    setError(null);
    setSummary(null);
    setResults(null);
    
    try {
      const data = await trackApiCall('create-backtest', async () => {
        const res = await fetch('/api/v1/backtests', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ strategy_name: strategyName, start_date: startDate, end_date: endDate, symbol }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      });
      
      setBacktestId(data.backtest_id);
      setStatus(data.status);
    } catch (e: any) {
      setError(e.message ?? 'Failed to create backtest');
    } finally {
      setCreating(false);
    }
  };

  const refreshStatus = async () => {
    if (!backtestId) return;
    
    try {
      const data = await trackApiCall('get-backtest', async () => {
        const res = await fetch(`/api/v1/backtests/${backtestId}`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      });
      
      setStatus(data.status);
      setSummary(data.summary ?? null);
      setResults(data.results ?? null);
    } catch (e: any) {
      setError(e.message ?? 'Failed to fetch backtest');
    }
  };

  useEffect(() => {
    if (!backtestId) return;
    const t = setInterval(refreshStatus, 3000);
    return () => clearInterval(t);
  }, [backtestId]);

  return (
    <Dashboard currentPage="Backtesting">
      <div className="space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Backtesting</h2>
            <p className="text-sm text-gray-500">Submit a backtest job and monitor status</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Input className="w-44" value={strategyName} onChange={(e) => setStrategyName(e.target.value)} placeholder="Strategy Name" />
            <Input className="w-36" value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} placeholder="Symbol" />
            <Input className="w-36" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            <Input className="w-36" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            <Button variant="primary" onClick={createBacktest} disabled={creating}>{creating ? 'Submitting…' : 'Create Backtest'}</Button>
          </div>
        </div>

        {error && <Card variant="outlined" className="border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</Card>}

        {backtestId && (
          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <div className="text-sm text-gray-500">Backtest ID</div>
                <div className="text-sm font-medium">{backtestId}</div>
              </div>
              <div className="space-y-1">
                <div className="text-sm text-gray-500">Status</div>
                <div className="text-sm font-medium">{status}</div>
              </div>
              <Button variant="secondary" onClick={refreshStatus}>Refresh</Button>
            </div>
            {summary && <div className="mt-4 text-sm text-gray-700">{summary}</div>}
          </Card>
        )}
      </div>
    </Dashboard>
  );
}

