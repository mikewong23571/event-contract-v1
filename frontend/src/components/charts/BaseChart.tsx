'use client';

import React, { useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface BaseChartProps {
  className?: string;
  title?: string;
  subtitle?: string;
  loading?: boolean;
  error?: string | null;
  noData?: boolean;
  height?: number;
  width?: number;
  children?: React.ReactNode;
  showRealTimeIndicator?: boolean;
  onRefresh?: () => void;
}

export interface ChartMetric {
  label: string;
  value: string | number;
  change?: {
    value: number;
    type: 'positive' | 'negative' | 'neutral';
  };
}

export interface ChartTimeRange {
  label: string;
  value: string;
  active?: boolean;
}

const BaseChart: React.FC<BaseChartProps> = ({
  className,
  title,
  subtitle,
  loading = false,
  error = null,
  noData = false,
  height = 400,
  width,
  children,
  showRealTimeIndicator = false,
  onRefresh,
}) => {
  const containerStyle = useMemo(() => ({
    height: `${height}px`,
    width: width ? `${width}px` : '100%',
  }), [height, width]);

  if (loading) {
    return (
      <div className={cn('chart-container', className)} style={containerStyle}>
        {title && (
          <div className="chart-header">
            <div>
              <h3 className="chart-title">{title}</h3>
              {subtitle && <p className="chart-subtitle">{subtitle}</p>}
            </div>
          </div>
        )}
        <div className="chart-loading">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-2 text-sm text-muted-foreground">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('chart-container', className)} style={containerStyle}>
        {title && (
          <div className="chart-header">
            <div>
              <h3 className="chart-title">{title}</h3>
              {subtitle && <p className="chart-subtitle">{subtitle}</p>}
            </div>
          </div>
        )}
        <div className="chart-error">
          <div className="text-destructive mb-2">
            <svg className="h-8 w-8 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <p className="text-sm text-destructive font-medium">图表加载失败</p>
          <p className="text-xs text-muted-foreground mt-1">{error}</p>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="mt-3 text-xs text-primary hover:text-primary/80 underline"
            >
              重试
            </button>
          )}
        </div>
      </div>
    );
  }

  if (noData) {
    return (
      <div className={cn('chart-container', className)} style={containerStyle}>
        {title && (
          <div className="chart-header">
            <div>
              <h3 className="chart-title">{title}</h3>
              {subtitle && <p className="chart-subtitle">{subtitle}</p>}
            </div>
          </div>
        )}
        <div className="chart-no-data">
          <div className="text-muted-foreground mb-2">
            <svg className="h-8 w-8 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p className="text-sm font-medium">暂无数据</p>
          <p className="text-xs mt-1">请稍后再试或检查数据源</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('chart-container', className)} style={containerStyle}>
      {(title || showRealTimeIndicator) && (
        <div className="chart-header">
          <div>
            {title && <h3 className="chart-title">{title}</h3>}
            {subtitle && <p className="chart-subtitle">{subtitle}</p>}
          </div>
          {showRealTimeIndicator && (
            <div className="realtime-indicator">
              <div className="realtime-dot"></div>
              <span>实时</span>
            </div>
          )}
        </div>
      )}
      <div className="relative flex-1">
        {children}
      </div>
    </div>
  );
};

export default BaseChart;

// 图表指标卡片组件
export const ChartMetricCard: React.FC<{
  metric: ChartMetric;
  className?: string;
}> = ({ metric, className }) => {
  // 防止 metric 为 undefined 的情况
  if (!metric) {
    return null;
  }

  return (
    <div className={cn('chart-metric-card', className)}>
      <div className="chart-metric-value">{metric.value ?? '--'}</div>
      <div className="chart-metric-label">{metric.label ?? ''}</div>
      {metric.change && (
        <div className={cn(
          'chart-metric-change',
          metric.change.type === 'positive' && 'chart-metric-positive',
          metric.change.type === 'negative' && 'chart-metric-negative'
        )}>
          {metric.change.type === 'positive' ? '+' : ''}{metric.change.value}%
        </div>
      )}
    </div>
  );
};

// 时间范围选择器组件
export const ChartTimeSelector: React.FC<{
  ranges: ChartTimeRange[];
  onSelect: (value: string) => void;
  className?: string;
}> = ({ ranges, onSelect, className }) => {
  return (
    <div className={cn('chart-controls', className)}>
      {ranges.map((range) => (
        <button
          key={range.value}
          onClick={() => onSelect(range.value)}
          className={cn(
            'chart-time-selector',
            range.active && 'active'
          )}
        >
          {range.label}
        </button>
      ))}
    </div>
  );
};