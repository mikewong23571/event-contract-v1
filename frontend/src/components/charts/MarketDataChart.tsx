'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { EnhancedLineChart, RealTimeChart, ChartMetricCard, type ChartMetric, type ChartTimeRange } from './index';
import { formatCurrency, formatNumber } from '@/lib/utils';

/**
 * MarketDataChart
 * Enhanced real-time market data visualization component.
 * Displays price movements over time with advanced features.
 *
 * Features:
 * - Enhanced responsive chart with animations
 * - Real-time and historical data modes
 * - Interactive time range selection
 * - Performance metrics display
 * - Advanced tooltips and indicators
 */

export interface MarketDataPoint {
  timestamp: string | number; // ISO 8601 string or Unix timestamp
  price: number;
  volume?: number;
  symbol: string;
  high?: number;
  low?: number;
  open?: number;
  close?: number;
}

export interface MarketDataChartProps {
  data?: MarketDataPoint[];
  symbol: string;
  height?: number;
  className?: string;
  showVolume?: boolean;
  realTime?: boolean;
  showMetrics?: boolean;
  interval?: '1m' | '5m' | '15m' | '1h' | '4h' | '1d';
}

function formatTimestamp(timestamp: string | number): string {
  try {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return String(timestamp);
    return date.toLocaleTimeString();
  } catch {
    return String(timestamp);
  }
}

function formatPrice(price: number): string {
  return price.toFixed(4);
}

export function MarketDataChart({ 
  data = [], 
  symbol, 
  height = 400, 
  className = '',
  showVolume = false,
  realTime = false,
  showMetrics = true,
  interval = '1m'
}: MarketDataChartProps) {
  const [selectedInterval, setSelectedInterval] = useState(interval);
  const [mockData, setMockData] = useState<MarketDataPoint[]>([]);
  const [loading, setLoading] = useState(false);

  // 如果没有提供数据，生成模拟数据
  useEffect(() => {
    if (data.length === 0) {
      setLoading(true);
      // 生成模拟数据
      const generateMockData = () => {
        const now = Date.now();
        const mockPoints: MarketDataPoint[] = [];
        let price = 100 + Math.random() * 50;
        
        for (let i = 0; i < 50; i++) {
          const timestamp = now - (49 - i) * 60000;
          const change = (Math.random() - 0.5) * 4;
          const open = price;
          price = Math.max(0.01, price + change);
          const high = Math.max(open, price) + Math.random() * 2;
          const low = Math.min(open, price) - Math.random() * 2;
          const close = price;
          const volume = Math.floor(Math.random() * 100000) + 10000;
          
          mockPoints.push({
            timestamp,
            price: close,
            volume,
            high,
            low,
            open,
            close,
            symbol,
          });
        }
        
        setMockData(mockPoints);
        setLoading(false);
      };
      
      setTimeout(generateMockData, 500);
    }
  }, [data.length, symbol]);

  const chartData = (data.length > 0 ? data : mockData).map(point => ({
    timestamp: typeof point.timestamp === 'number' ? point.timestamp : new Date(point.timestamp).getTime(),
    value: point.price,
    volume: point.volume || 0,
    high: point.high || point.price,
    low: point.low || point.price,
    open: point.open || point.price,
    close: point.close || point.price,
  }));

  // 计算指标
  const metrics: ChartMetric[] = useMemo(() => {
    if (chartData.length === 0) return [];
    
    const latestData = chartData[chartData.length - 1];
    const previousData = chartData.length > 1 ? chartData[chartData.length - 2] : null;
    const change = previousData ? latestData.value - previousData.value : 0;
    const changePercent = previousData && previousData.value > 0 ? (change / previousData.value) * 100 : 0;
    
    const high24h = Math.max(...chartData.map(d => d.high));
    const low24h = Math.min(...chartData.map(d => d.low));
    const volume24h = chartData.reduce((sum, d) => sum + d.volume, 0);
    
    return [
      {
        label: '当前价格',
        value: formatCurrency(latestData.value),
        change: {
          value: changePercent,
          type: changePercent > 0 ? 'positive' : changePercent < 0 ? 'negative' : 'neutral',
        },
      },
      {
        label: '24h最高',
        value: formatCurrency(high24h),
      },
      {
        label: '24h最低',
        value: formatCurrency(low24h),
      },
      {
        label: '24h成交量',
        value: formatNumber(volume24h),
      },
    ];
  }, [chartData]);

  // 时间范围配置
  const timeRanges: ChartTimeRange[] = useMemo(() => [
    { label: '1分钟', value: '1m', active: selectedInterval === '1m' },
    { label: '5分钟', value: '5m', active: selectedInterval === '5m' },
    { label: '15分钟', value: '15m', active: selectedInterval === '15m' },
    { label: '1小时', value: '1h', active: selectedInterval === '1h' },
    { label: '4小时', value: '4h', active: selectedInterval === '4h' },
    { label: '1天', value: '1d', active: selectedInterval === '1d' },
  ], [selectedInterval]);

  const handleTimeRangeChange = (range: string) => {
    setSelectedInterval(range as typeof interval);
  };

  // 如果是实时模式，使用RealTimeChart
  if (realTime) {
    return (
      <div className={className}>
        <RealTimeChart
          symbol={symbol}
          title={`${symbol} 实时行情`}
          height={height}
          showMetrics={showMetrics}
          showControls={true}
        />
      </div>
    );
  }

  return (
    <div className={`w-full ${className}`}>
      {showMetrics && metrics.length > 0 && (
        <div className="mb-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          {metrics.map((metric, index) => (
            <ChartMetricCard key={index} metric={metric} />
          ))}
        </div>
      )}
      
      <EnhancedLineChart
        data={chartData}
        title={`${symbol} 价格走势`}
        height={height}
        loading={loading}
        timeRanges={timeRanges}
        onTimeRangeChange={handleTimeRangeChange}
        lines={[
          {
            dataKey: 'value',
            name: '价格',
            color: '#3b82f6',
            strokeWidth: 2,
            dot: false,
            activeDot: true,
          }
        ]}
        showGrid={true}
        showTooltip={true}
        showLegend={false}
        animate={true}
      />
    </div>
  );
}

export default MarketDataChart;