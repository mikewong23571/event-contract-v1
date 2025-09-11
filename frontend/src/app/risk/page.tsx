"use client";

import { useEffect, useState } from 'react';
import Dashboard from '@/components/layout/Dashboard';

type RiskParams = {
  max_position_size: number;
  stop_loss_percentage: number;
  take_profit_percentage: number;
  max_daily_loss: number;
  max_concurrent_trades: number;
  min_confidence_level: 'LOW' | 'MEDIUM' | 'HIGH';
};

export default function RiskPage() {
  const [params, setParams] = useState<RiskParams | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const load = async () => {
    setError(null);
    try {
      const res = await fetch('/api/v1/risk-parameters', { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setParams({
        max_position_size: data.max_position_size,
        stop_loss_percentage: data.stop_loss_percentage,
        take_profit_percentage: data.take_profit_percentage,
        max_daily_loss: data.max_daily_loss,
        max_concurrent_trades: data.max_concurrent_trades,
        min_confidence_level: data.min_confidence_level,
      });
    } catch (e: any) {
      setError(e.message ?? 'Failed to load risk parameters');
    }
  };

  const save = async () => {
    if (!params) return;
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const res = await fetch('/api/v1/risk-parameters', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setSaved(true);
    } catch (e: any) {
      setError(e.message ?? 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <Dashboard currentPage="Risk Management">
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Risk Parameters</h2>
          <p className="text-sm text-gray-500">Tune risk settings used by runtime and backtests</p>
        </div>

        {error && <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

        {params && (
          <div className="card space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="space-y-1">
                <span className="text-sm text-gray-600">Max Position Size</span>
                <input className="input" type="number" value={params.max_position_size} onChange={(e) => setParams({ ...params, max_position_size: Number(e.target.value) })} />
              </label>
              <label className="space-y-1">
                <span className="text-sm text-gray-600">Max Daily Loss</span>
                <input className="input" type="number" value={params.max_daily_loss} onChange={(e) => setParams({ ...params, max_daily_loss: Number(e.target.value) })} />
              </label>
              <label className="space-y-1">
                <span className="text-sm text-gray-600">Stop Loss %</span>
                <input className="input" type="number" step="0.01" value={params.stop_loss_percentage} onChange={(e) => setParams({ ...params, stop_loss_percentage: Number(e.target.value) })} />
              </label>
              <label className="space-y-1">
                <span className="text-sm text-gray-600">Take Profit %</span>
                <input className="input" type="number" step="0.01" value={params.take_profit_percentage} onChange={(e) => setParams({ ...params, take_profit_percentage: Number(e.target.value) })} />
              </label>
              <label className="space-y-1">
                <span className="text-sm text-gray-600">Max Concurrent Trades</span>
                <input className="input" type="number" value={params.max_concurrent_trades} onChange={(e) => setParams({ ...params, max_concurrent_trades: Number(e.target.value) })} />
              </label>
              <label className="space-y-1">
                <span className="text-sm text-gray-600">Min Confidence</span>
                <select className="input" value={params.min_confidence_level} onChange={(e) => setParams({ ...params, min_confidence_level: e.target.value as any })}>
                  <option value="LOW">LOW</option>
                  <option value="MEDIUM">MEDIUM</option>
                  <option value="HIGH">HIGH</option>
                </select>
              </label>
            </div>
            <div className="flex items-center gap-2">
              <button className="btn btn-primary" onClick={save} disabled={saving}>{saving ? 'Saving…' : 'Save'}</button>
              {saved && <span className="text-sm text-green-600">Saved!</span>}
            </div>
          </div>
        )}
      </div>
    </Dashboard>
  );
}

