'use client';

import React, { useMemo, useCallback } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import BaseChart, { ChartTimeSelector, type ChartTimeRange } from './BaseChart';
import { cn, formatNumber, formatCurrency } from '@/lib/utils';

export interface AreaChartDataPoint {
  timestamp: string | number;
  [key: string]: string | number;
}

export interface AreaConfig {
  dataKey: string;
  name: string;
  fill: string;
  stroke?: string;
  strokeWidth?: number;
  fillOpacity?: number;
  stackId?: string;
}

export interface EnhancedAreaChartProps {
  data: AreaChartDataPoint[];
  areas: AreaConfig[];
  title?: string;
  subtitle?: string;
  className?: string;
  height?: number;
  width?: number;
  loading?: boolean;
  error?: string | null;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  showRealTimeIndicator?: boolean;
  timeRanges?: ChartTimeRange[];
  onTimeRangeChange?: (range: string) => void;
  xAxisDataKey?: string;
  xAxisFormatter?: (value: any) => string;
  yAxisFormatter?: (value: any) => string;
  tooltipFormatter?: (value: any, name: string) => [string, string];
  referenceLine?: {
    y?: number;
    x?: string | number;
    stroke?: string;
    strokeDasharray?: string;
    label?: string;
  };
  onRefresh?: () => void;
  animate?: boolean;
  stacked?: boolean;
  gradient?: boolean;
}

const EnhancedAreaChart: React.FC<EnhancedAreaChartProps> = ({
  data,
  areas,
  title,
  subtitle,
  className,
  height = 400,
  width,
  loading = false,
  error = null,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  showRealTimeIndicator = false,
  timeRanges,
  onTimeRangeChange,
  xAxisDataKey = 'timestamp',
  xAxisFormatter,
  yAxisFormatter,
  tooltipFormatter,
  referenceLine,
  onRefresh,
  animate = true,
  stacked = false,
  gradient = true,
}) => {
  const noData = !data || data.length === 0;

  const defaultXAxisFormatter = useCallback((value: any) => {
    if (typeof value === 'number') {
      return new Date(value).toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
      });
    }
    return String(value);
  }, []);

  const defaultYAxisFormatter = useCallback((value: any) => {
    return formatNumber(value, 2);
  }, []);

  const defaultTooltipFormatter = useCallback((value: any, name: string) => {
    const formattedValue = typeof value === 'number' ? formatNumber(value, 4) : String(value);
    return [formattedValue, name];
  }, []);

  const customTooltip = useMemo(() => {
    if (!showTooltip) return undefined;

    return ({ active, payload, label }: any) => {
      if (!active || !payload || !payload.length) return null;

      return (
        <div className="chart-tooltip">
          <p className="font-medium mb-2">
            {xAxisFormatter ? xAxisFormatter(label) : defaultXAxisFormatter(label)}
          </p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center gap-2 text-sm">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-muted-foreground">{entry.name}:</span>
              <span className="font-medium">
                {tooltipFormatter
                  ? tooltipFormatter(entry.value, entry.name)[0]
                  : defaultTooltipFormatter(entry.value, entry.name)[0]}
              </span>
            </div>
          ))}
        </div>
      );
    };
  }, [showTooltip, xAxisFormatter, tooltipFormatter, defaultXAxisFormatter, defaultTooltipFormatter]);

  // 生成渐变定义
  const gradientDefs = useMemo(() => {
    if (!gradient) return null;

    return (
      <defs>
        {areas.map((area, index) => {
          const gradientId = `gradient-${area.dataKey}`;
          return (
            <linearGradient key={gradientId} id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={area.fill} stopOpacity={0.8} />
              <stop offset="95%" stopColor={area.fill} stopOpacity={0.1} />
            </linearGradient>
          );
        })}
      </defs>
    );
  }, [gradient, areas]);

  const chartContent = useMemo(() => {
    if (noData) return null;

    return (
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          {gradientDefs}
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              className="chart-grid-line"
              stroke="hsl(var(--border))"
            />
          )}
          <XAxis
            dataKey={xAxisDataKey}
            tickFormatter={xAxisFormatter || defaultXAxisFormatter}
            className="chart-axis-text"
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
          />
          <YAxis
            tickFormatter={yAxisFormatter || defaultYAxisFormatter}
            className="chart-axis-text"
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
          />
          {showTooltip && <Tooltip content={customTooltip} />}
          {showLegend && (
            <Legend
              wrapperStyle={{
                paddingTop: '20px',
                fontSize: '12px',
                color: 'hsl(var(--muted-foreground))',
              }}
            />
          )}
          {referenceLine && (
            <ReferenceLine
              y={referenceLine.y}
              x={referenceLine.x}
              stroke={referenceLine.stroke || 'hsl(var(--muted-foreground))'}
              strokeDasharray={referenceLine.strokeDasharray || '5 5'}
              label={referenceLine.label}
            />
          )}
          {areas.map((area, index) => {
            const fillValue = gradient ? `url(#gradient-${area.dataKey})` : area.fill;
            return (
              <Area
                key={area.dataKey}
                type="monotone"
                dataKey={area.dataKey}
                name={area.name}
                stackId={stacked ? (area.stackId || 'default') : undefined}
                stroke={area.stroke || area.fill}
                strokeWidth={area.strokeWidth || 2}
                fill={fillValue}
                fillOpacity={area.fillOpacity || (gradient ? 1 : 0.6)}
                className="chart-data-area"
                animationDuration={animate ? 1000 : 0}
                animationBegin={animate ? index * 100 : 0}
              />
            );
          })}
        </AreaChart>
      </ResponsiveContainer>
    );
  }, [data, areas, showGrid, showTooltip, showLegend, xAxisDataKey, xAxisFormatter, yAxisFormatter, customTooltip, referenceLine, animate, stacked, gradient, gradientDefs, noData, defaultXAxisFormatter, defaultYAxisFormatter]);

  return (
    <BaseChart
      className={cn('realtime-chart', className)}
      title={title}
      subtitle={subtitle}
      loading={loading}
      error={error}
      noData={noData}
      height={height}
      width={width}
      showRealTimeIndicator={showRealTimeIndicator}
      onRefresh={onRefresh}
    >
      <div className="flex flex-col h-full">
        {timeRanges && onTimeRangeChange && (
          <div className="mb-4">
            <ChartTimeSelector
              ranges={timeRanges}
              onSelect={onTimeRangeChange}
            />
          </div>
        )}
        <div className="flex-1">
          {chartContent}
        </div>
      </div>
    </BaseChart>
  );
};

export default EnhancedAreaChart;

// 预设配置
export const presetConfigs = {
  // 累积收益配置
  cumulativeReturn: {
    areas: [
      {
        dataKey: 'cumulativeReturn',
        name: '累积收益',
        fill: 'hsl(var(--primary))',
        fillOpacity: 0.6,
      },
    ],
    yAxisFormatter: (value: number) => `${(value * 100).toFixed(2)}%`,
    tooltipFormatter: (value: number, name: string) => [
      `${(value * 100).toFixed(4)}%`,
      name,
    ] as [string, string],
  },
  // 资产分布配置（堆叠）
  assetDistribution: {
    areas: [
      {
        dataKey: 'stocks',
        name: '股票',
        fill: 'hsl(var(--primary))',
        stackId: 'assets',
      },
      {
        dataKey: 'bonds',
        name: '债券',
        fill: 'hsl(var(--secondary))',
        stackId: 'assets',
      },
      {
        dataKey: 'cash',
        name: '现金',
        fill: 'hsl(var(--accent))',
        stackId: 'assets',
      },
    ],
    stacked: true,
    yAxisFormatter: (value: number) => formatCurrency(value),
  },
  // 风险指标配置
  riskMetrics: {
    areas: [
      {
        dataKey: 'var',
        name: 'VaR',
        fill: 'hsl(var(--destructive))',
        fillOpacity: 0.4,
      },
      {
        dataKey: 'expectedShortfall',
        name: 'ES',
        fill: 'hsl(var(--warning))',
        fillOpacity: 0.4,
      },
    ],
    yAxisFormatter: (value: number) => `${(value * 100).toFixed(2)}%`,
  },
};