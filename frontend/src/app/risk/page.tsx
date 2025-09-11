"use client";

import { useEffect, useState } from 'react';
import Dashboard from '@/components/layout/Dashboard';
import { 
  Input, 
  Button, 
  Select, 
  PageHeader, 
  FormGrid, 
  ErrorBanner, 
  SuccessNote, 
  FormLayout
} from '@/components/ui';

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
  
  // Form validation
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const errors: Record<string, string> = {};
    
    if (!params) return false;
    
    if (params.max_position_size <= 0) {
      errors.max_position_size = '最大仓位必须大于0';
    }
    
    if (params.stop_loss_percentage <= 0 || params.stop_loss_percentage >= 100) {
      errors.stop_loss_percentage = '止损百分比必须在0-100之间';
    }
    
    if (params.take_profit_percentage <= 0) {
      errors.take_profit_percentage = '止盈百分比必须大于0';
    }
    
    if (params.max_daily_loss <= 0) {
      errors.max_daily_loss = '最大日损失必须大于0';
    }
    
    if (params.max_concurrent_trades <= 0) {
      errors.max_concurrent_trades = '最大并发交易数必须大于0';
    }
    
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

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
      setError(e.message ?? '加载风险参数失败');
    }
  };

  const save = async () => {
    if (!params || !validateForm()) {
      setError('请检查输入参数');
      return;
    }
    
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
      setTimeout(() => setSaved(false), 3000);
    } catch (e: any) {
      setError(e.message ?? '保存失败');
    } finally {
      setSaving(false);
    }
  };
  
  // Confidence level options
  const confidenceOptions = [
    { value: 'LOW', label: '低' },
    { value: 'MEDIUM', label: '中' },
    { value: 'HIGH', label: '高' },
  ];

  useEffect(() => { load(); }, []);

  return (
    <Dashboard currentPage="Risk Management">
      <div className="space-y-6">
        <PageHeader 
          title="风险管理" 
          subtitle="调整运行时和回测使用的风险设置"
        />
        
        {error && (
          <ErrorBanner 
            message={error} 
            onClose={() => setError(null)}
          />
        )}
        
        {saved && (
          <SuccessNote 
            message="风险参数已成功保存"
            durationMs={3000}
          />
        )}

        {params && (
          <div className="bg-white rounded-lg border p-6">
            <FormLayout
              actions={(
                <Button 
                  variant="primary" 
                  onClick={save} 
                  disabled={saving}
                >
                  {saving ? '保存中...' : '保存设置'}
                </Button>
              )}
            >
              <FormGrid colsSm={1} colsMd={2} colsLg={3}>
                <Input 
                  label="最大仓位大小"
                  type="number" 
                  value={params.max_position_size} 
                  onChange={(e) => setParams({ ...params, max_position_size: Number(e.target.value) })} 
                  error={fieldErrors.max_position_size}
                />
                <Input 
                  label="最大日损失"
                  type="number" 
                  value={params.max_daily_loss} 
                  onChange={(e) => setParams({ ...params, max_daily_loss: Number(e.target.value) })} 
                  error={fieldErrors.max_daily_loss}
                />
                <Input 
                  label="止损百分比 (%)"
                  type="number" 
                  step="0.01" 
                  value={params.stop_loss_percentage} 
                  onChange={(e) => setParams({ ...params, stop_loss_percentage: Number(e.target.value) })} 
                  error={fieldErrors.stop_loss_percentage}
                />
                <Input 
                  label="止盈百分比 (%)"
                  type="number" 
                  step="0.01" 
                  value={params.take_profit_percentage} 
                  onChange={(e) => setParams({ ...params, take_profit_percentage: Number(e.target.value) })} 
                  error={fieldErrors.take_profit_percentage}
                />
                <Input 
                  label="最大并发交易数"
                  type="number" 
                  value={params.max_concurrent_trades} 
                  onChange={(e) => setParams({ ...params, max_concurrent_trades: Number(e.target.value) })} 
                  error={fieldErrors.max_concurrent_trades}
                />
                <Select 
                  label="最小置信度"
                  options={confidenceOptions}
                  value={params.min_confidence_level}
                  onChange={(e) => setParams({ ...params, min_confidence_level: e.target.value as RiskParams['min_confidence_level'] })}
                />
              </FormGrid>
            </FormLayout>
          </div>
        )}
      </div>
    </Dashboard>
  );
}

