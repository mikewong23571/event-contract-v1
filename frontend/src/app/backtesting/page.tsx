"use client";

import { useEffect, useState } from 'react';
import Dashboard from '@/components/layout/Dashboard';
import { LazyBacktestResultsWithFallback } from '@/components/lazy/LazyComponents';
import { useRenderTimeTracker, useApiTracker } from '@/stores/performanceStore';
import { 
  Input, 
  Button, 
  Card, 
  CardContent, 
  PageHeader, 
  ControlBar, 
  FormGrid, 
  ErrorBanner, 
  SuccessNote, 
  StatusIndicator 
} from '@/components/ui';

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
  const [success, setSuccess] = useState<string | null>(null);
  const [backtestId, setBacktestId] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);
  
  // Form validation
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const errors: Record<string, string> = {};
    
    if (!strategyName.trim()) {
      errors.strategyName = '策略名称不能为空';
    }
    
    if (!symbol.trim()) {
      errors.symbol = '交易对不能为空';
    }
    
    if (!startDate) {
      errors.startDate = '开始日期不能为空';
    }
    
    if (!endDate) {
      errors.endDate = '结束日期不能为空';
    }
    
    if (startDate && endDate && new Date(startDate) >= new Date(endDate)) {
      errors.endDate = '结束日期必须晚于开始日期';
    }
    
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const createBacktest = async () => {
    if (!validateForm()) {
      setError('请检查表单输入');
      return;
    }
    
    setCreating(true);
    setError(null);
    setSuccess(null);
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
      setSuccess('回测任务创建成功');
    } catch (e: any) {
      setError(e.message ?? '创建回测失败');
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
        <PageHeader 
          title="策略回测" 
          subtitle="创建并监控回测任务的执行状态"
        />
        
        <ControlBar>
          <FormGrid colsSm={1} colsMd={2} colsLg={4}>
            <Input 
              label="策略名称"
              value={strategyName} 
              onChange={(e) => setStrategyName(e.target.value)} 
              placeholder="RSI Strategy" 
              error={fieldErrors.strategyName}
            />
            <Input 
              label="交易对"
              value={symbol} 
              onChange={(e) => setSymbol(e.target.value.toUpperCase())} 
              placeholder="BTCUSDT" 
              error={fieldErrors.symbol}
            />
            <Input 
              label="开始日期"
              type="date" 
              value={startDate} 
              onChange={(e) => setStartDate(e.target.value)}
              error={fieldErrors.startDate}
            />
            <Input 
              label="结束日期"
              type="date" 
              value={endDate} 
              onChange={(e) => setEndDate(e.target.value)}
              error={fieldErrors.endDate}
            />
          </FormGrid>
          
          <div className="flex justify-end">
            <Button 
              variant="primary" 
              onClick={createBacktest} 
              disabled={creating}
              className="min-w-[120px]"
            >
              {creating ? '提交中...' : '创建回测'}
            </Button>
          </div>
        </ControlBar>

        {error && (
          <ErrorBanner 
            message={error} 
            onClose={() => setError(null)}
          />
        )}
        
        {success && (
          <SuccessNote 
            message={success} 
            onClose={() => setSuccess(null)}
          />
        )}

        {backtestId && (
          <Card>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-1">
                  <div className="text-sm text-muted-foreground">回测ID</div>
                  <div className="text-sm font-medium font-mono">{backtestId}</div>
                </div>
                <div className="space-y-1">
                  <div className="text-sm text-muted-foreground">执行状态</div>
                  <div className="flex items-center gap-2">
                    <StatusIndicator 
                      status={status === 'completed' ? 'success' : status === 'failed' ? 'error' : 'loading'} 
                      text={status || '未知'}
                      size="sm"
                    />
                    <span className="text-sm font-medium">{status}</span>
                  </div>
                </div>
                <div className="flex justify-end">
                  <Button variant="secondary" onClick={refreshStatus}>
                    刷新状态
                  </Button>
                </div>
              </div>
              
              {summary && (
                <div className="mt-4 p-3 bg-muted/50 rounded-md">
                  <div className="text-sm text-muted-foreground mb-1">执行摘要</div>
                  <div className="text-sm">{summary}</div>
                </div>
              )}
              
              {results && (
                <div className="mt-4">
                  <LazyBacktestResultsWithFallback result={results} />
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </Dashboard>
  );
}

