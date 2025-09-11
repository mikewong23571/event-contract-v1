"use client";

import { useEffect, useState } from 'react';
import Dashboard from '@/components/layout/Dashboard';
import SignalList from '@/components/signals/SignalList';
import { TradingSignal as UiSignal } from '@/components/signals/SignalCard';
import { 
  Input, 
  Button, 
  PageHeader, 
  ControlBar, 
  FormGrid, 
  ErrorBanner 
} from '@/components/ui';

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
  
  // Form validation
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const errors: Record<string, string> = {};
    
    if (!symbol.trim()) {
      errors.symbol = '交易对不能为空';
    }
    
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

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
      setError(e.message ?? '加载信号失败');
    } finally {
      setLoading(false);
    }
  };

  const generateSignal = async () => {
    if (!validateForm()) {
      setError('请检查输入参数');
      return;
    }
    
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
      setError(e.message ?? '生成信号失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, []);



  return (
    <Dashboard currentPage="Signals">
      <div className="space-y-6">
        <PageHeader 
          title="交易信号" 
          subtitle="生成和查看最新的交易信号"
        />
        
        <ControlBar>
          <FormGrid colsSm={1} colsMd={2} colsLg={3}>
            <Input 
              label="交易对"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="BTCUSDT"
              error={fieldErrors.symbol}
            />
            <div className="flex items-end gap-2">
              <Button 
                onClick={generateSignal} 
                variant="primary" 
                disabled={loading}
                className="flex-1"
              >
                {loading ? '生成中...' : '生成信号'}
              </Button>
              <Button 
                onClick={fetchSignals} 
                variant="secondary" 
                disabled={loading}
                className="flex-1"
              >
                刷新
              </Button>
            </div>
          </FormGrid>
        </ControlBar>
        
        {error && (
          <ErrorBanner 
            message={error} 
            onClose={() => setError(null)}
          />
        )}
        
        <div className="bg-white rounded-lg border p-6">
          <SignalList signals={signals} loading={loading} />
        </div>
      </div>
    </Dashboard>
  );
}

