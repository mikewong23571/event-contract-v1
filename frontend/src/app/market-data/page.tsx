"use client";

import { useCallback, useEffect, useState } from 'react';
import Dashboard from '@/components/layout/Dashboard';
import MarketDataChart from '@/components/charts/MarketDataChart';
import { 
  Input, 
  Button, 
  Select, 
  PageHeader, 
  FormGrid, 
  ErrorBanner, 
  FormLayout
} from '@/components/ui';

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

  const loadData = useCallback(async () => {
    if (!validateForm()) {
      setError('请检查输入参数');
      return;
    }
    
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
      setError(e.message ?? '加载市场数据失败');
    } finally {
      setLoading(false);
    }
  }, [symbol, interval, limit]);

  useEffect(() => { loadData(); }, [loadData]);

  // Interval options
  const intervalOptions = [
    { value: '1m', label: '1分钟' },
    { value: '5m', label: '5分钟' },
    { value: '15m', label: '15分钟' },
    { value: '1h', label: '1小时' },
  ];
  
  // Limit options
  const limitOptions = [
    { value: 50, label: '50条' },
    { value: 100, label: '100条' },
    { value: 200, label: '200条' },
    { value: 500, label: '500条' },
  ];

  return (
    <Dashboard currentPage="Market Data">
      <div className="space-y-6">
        <PageHeader 
          title="市场数据" 
          subtitle="实时K线数据查看与分析"
        />
        
        <FormLayout
          actions={(
            <Button 
              variant="primary" 
              onClick={loadData} 
              disabled={loading}
            >
              {loading ? '加载中...' : '刷新数据'}
            </Button>
          )}
        >
          <FormGrid colsSm={1} md={2} lg={3}>
            <Input 
              label="交易对"
              value={symbol} 
              onChange={(e) => setSymbol(e.target.value.toUpperCase())} 
              placeholder="BTCUSDT"
              error={fieldErrors.symbol}
            />
            <Select 
              label="时间间隔"
              options={intervalOptions}
              value={interval}
              onChange={(e) => setInterval(e.target.value as Interval)}
            />
            <Select 
              label="数据条数"
              options={limitOptions}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
            />
          </FormGrid>
        </FormLayout>
        
        {error && (
          <ErrorBanner 
            message={error} 
            onClose={() => setError(null)}
          />
        )}
        
        <div className="bg-white rounded-lg border p-6">
          <MarketDataChart data={points} symbol={symbol} height={360} />
        </div>
      </div>
    </Dashboard>
  );
}

