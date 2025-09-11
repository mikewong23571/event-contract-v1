'use client';

import React, { useMemo, useCallback } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts';
import BaseChart, { ChartTimeSelector, type ChartTimeRange } from './BaseChart';
import { cn, formatNumber, formatCurrency } from '@/lib/utils';

export interface BarChartDataPoint {
  name: string;
  [key: string]: string | number;
}

export interface BarConfig {
  dataKey: string;
  name: string;
  fill: string;
  stroke?: string;
  strokeWidth?: number;
  radius?: [number, number, number, number];
  stackId?: string;
}

export interface EnhancedBarChartProps {
  data: BarChartDataPoint[];
  bars: BarConfig[];
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
  horizontal?: boolean;
  colorByValue?: boolean;
  colorScale?: string[];
  onBarClick?: (data: any, index: number) => void;
}

const EnhancedBarChart: React.FC<EnhancedBarChartProps> = ({
  data,
  bars,
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
  xAxisDataKey = 'name',
  xAxisFormatter,
  yAxisFormatter,
  tooltipFormatter,
  referenceLine,
  onRefresh,
  animate = true,
  stacked = false,
  horizontal = false,
  colorByValue = false,
  colorScale,
  onBarClick,
}) => {
  const noData = !data || data.length === 0;

  const defaultXAxisFormatter = useCallback((value: any) => {
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
                className="w-3 h-3 rounded-sm"
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

  // 生成颜色映射
  const getBarColor = useCallback((value: number, index: number, dataKey: string) => {
    if (!colorByValue || !colorScale) {
      return bars.find(bar => bar.dataKey === dataKey)?.fill || 'hsl(var(--primary))';
    }

    const maxValue = Math.max(...data.map(d => Number(d[dataKey]) || 0));
    const minValue = Math.min(...data.map(d => Number(d[dataKey]) || 0));
    const normalizedValue = (value - minValue) / (maxValue - minValue);
    const colorIndex = Math.floor(normalizedValue * (colorScale.length - 1));
    return colorScale[Math.min(colorIndex, colorScale.length - 1)];
  }, [colorByValue, colorScale, bars, data]);

  const chartContent = useMemo(() => {
    if (noData) return null;

    const ChartComponent = horizontal ? BarChart : BarChart;
    const chartProps = horizontal
      ? { layout: 'horizontal' as const }
      : {};

    return (
      <ResponsiveContainer width="100%" height="100%">
        <ChartComponent
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          {...chartProps}
        >
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              className="chart-grid-line"
              stroke="hsl(var(--border))"
            />
          )}
          <XAxis
            dataKey={horizontal ? undefined : xAxisDataKey}
            type={horizontal ? 'number' : 'category'}
            tickFormatter={horizontal ? (yAxisFormatter || defaultYAxisFormatter) : (xAxisFormatter || defaultXAxisFormatter)}
            className="chart-axis-text"
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
          />
          <YAxis
            dataKey={horizontal ? xAxisDataKey : undefined}
            type={horizontal ? 'category' : 'number'}
            tickFormatter={horizontal ? (xAxisFormatter || defaultXAxisFormatter) : (yAxisFormatter || defaultYAxisFormatter)}
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
              y={horizontal ? undefined : referenceLine.y}
              x={horizontal ? referenceLine.y : referenceLine.x}
              stroke={referenceLine.stroke || 'hsl(var(--muted-foreground))'}
              strokeDasharray={referenceLine.strokeDasharray || '5 5'}
              label={referenceLine.label}
            />
          )}
          {bars.map((bar, index) => (
            <Bar
              key={bar.dataKey}
              dataKey={bar.dataKey}
              name={bar.name}
              fill={bar.fill}
              stroke={bar.stroke}
              strokeWidth={bar.strokeWidth || 0}
              radius={bar.radius || [0, 0, 0, 0]}
              stackId={stacked ? (bar.stackId || 'default') : undefined}
              animationDuration={animate ? 1000 : 0}
              animationBegin={animate ? index * 100 : 0}
              onClick={onBarClick}
              className="transition-opacity hover:opacity-80 cursor-pointer"
            >
              {colorByValue && data.map((entry, entryIndex) => (
                <Cell
                  key={`cell-${entryIndex}`}
                  fill={getBarColor(Number(entry[bar.dataKey]) || 0, entryIndex, bar.dataKey)}
                />
              ))}
            </Bar>
          ))}
        </ChartComponent>
      </ResponsiveContainer>
    );
  }, [data, bars, showGrid, showTooltip, showLegend, xAxisDataKey, xAxisFormatter, yAxisFormatter, customTooltip, referenceLine, animate, stacked, horizontal, colorByValue, getBarColor, onBarClick, noData, defaultXAxisFormatter, defaultYAxisFormatter]);

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

export default EnhancedBarChart;

// 预设配置
export const presetConfigs = {
  // 收益对比配置
  returnComparison: {
    bars: [
      {
        dataKey: 'return',
        name: '收益率',
        fill: 'hsl(var(--primary))',
        radius: [4, 4, 0, 0] as [number, number, number, number],
      },
    ],
    yAxisFormatter: (value: number) => `${(value * 100).toFixed(2)}%`,
    tooltipFormatter: (value: number, name: string) => [
      `${(value * 100).toFixed(4)}%`,
      name,
    ] as [string, string],
    colorByValue: true,
    colorScale: [
      'hsl(var(--destructive))',
      'hsl(var(--warning))',
      'hsl(var(--success))',
    ],
  },
  // 行业分布配置
  sectorDistribution: {
    bars: [
      {
        dataKey: 'weight',
        name: '权重',
        fill: 'hsl(var(--primary))',
        radius: [4, 4, 0, 0] as [number, number, number, number],
      },
    ],
    yAxisFormatter: (value: number) => `${(value * 100).toFixed(1)}%`,
    horizontal: true,
  },
  // 多策略对比配置
  strategyComparison: {
    bars: [
      {
        dataKey: 'strategy1',
        name: '策略1',
        fill: 'hsl(var(--primary))',
        radius: [4, 4, 0, 0] as [number, number, number, number],
      },
      {
        dataKey: 'strategy2',
        name: '策略2',
        fill: 'hsl(var(--secondary))',
        radius: [4, 4, 0, 0] as [number, number, number, number],
      },
      {
        dataKey: 'strategy3',
        name: '策略3',
        fill: 'hsl(var(--accent))',
        radius: [4, 4, 0, 0] as [number, number, number, number],
      },
    ],
    yAxisFormatter: (value: number) => formatCurrency(value),
  },
};