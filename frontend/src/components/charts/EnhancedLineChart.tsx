'use client';

import React, { useMemo, useCallback } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import BaseChart, { ChartMetricCard, ChartTimeSelector, type ChartTimeRange } from './BaseChart';
import { cn, formatNumber, formatCurrency } from '@/lib/utils';

export interface LineChartDataPoint {
  timestamp: string | number;
  [key: string]: string | number;
}

export interface LineConfig {
  dataKey: string;
  name: string;
  color: string;
  strokeWidth?: number;
  strokeDasharray?: string;
  dot?: boolean;
  activeDot?: boolean;
}

export interface EnhancedLineChartProps {
  data: LineChartDataPoint[];
  lines: LineConfig[];
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
}

const EnhancedLineChart: React.FC<EnhancedLineChartProps> = ({
  data,
  lines,
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

  const chartContent = useMemo(() => {
    if (noData) return null;

    return (
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
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
          {lines.map((line, index) => (
            <Line
              key={line.dataKey}
              type="monotone"
              dataKey={line.dataKey}
              name={line.name}
              stroke={line.color}
              strokeWidth={line.strokeWidth || 2}
              strokeDasharray={line.strokeDasharray}
              dot={line.dot !== false}
              activeDot={line.activeDot !== false ? { r: 4, className: 'chart-data-point' } : false}
              className="chart-data-line"
              animationDuration={animate ? 1000 : 0}
              animationBegin={animate ? index * 100 : 0}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }, [data, lines, showGrid, showTooltip, showLegend, xAxisDataKey, xAxisFormatter, yAxisFormatter, customTooltip, referenceLine, animate, noData, defaultXAxisFormatter, defaultYAxisFormatter]);

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

export default EnhancedLineChart;

// 预设配置
export const presetConfigs = {
  // 价格图表配置
  price: {
    lines: [
      {
        dataKey: 'price',
        name: '价格',
        color: 'hsl(var(--primary))',
        strokeWidth: 2,
      },
    ],
    yAxisFormatter: (value: number) => formatCurrency(value),
    tooltipFormatter: (value: number, name: string) => [
      formatCurrency(value),
      name,
    ] as [string, string],
  },
  // 成交量图表配置
  volume: {
    lines: [
      {
        dataKey: 'volume',
        name: '成交量',
        color: 'hsl(var(--secondary))',
        strokeWidth: 2,
      },
    ],
    yAxisFormatter: (value: number) => formatNumber(value, 0),
  },
  // 多指标对比配置
  comparison: {
    lines: [
      {
        dataKey: 'value1',
        name: '指标1',
        color: 'hsl(var(--primary))',
        strokeWidth: 2,
      },
      {
        dataKey: 'value2',
        name: '指标2',
        color: 'hsl(var(--secondary))',
        strokeWidth: 2,
        strokeDasharray: '5 5',
      },
    ],
  },
};