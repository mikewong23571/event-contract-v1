'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import EnhancedLineChart from './EnhancedLineChart';
import { ChartMetricCard, type ChartMetric, type ChartTimeRange } from './BaseChart';
import { cn, formatNumber, formatCurrency, formatPercentage } from '@/lib/utils';

export interface RealTimeDataPoint {
  timestamp: number;
  price: number;
  volume: number;
  change?: number;
  changePercent?: number;
}

export interface RealTimeChartProps {
  symbol: string;
  title?: string;
  className?: string;
  height?: number;
  maxDataPoints?: number;
  updateInterval?: number;
  showMetrics?: boolean;
  showControls?: boolean;
  onDataUpdate?: (data: RealTimeDataPoint[]) => void;
  dataSource?: () => Promise<RealTimeDataPoint>;
}

const RealTimeChart: React.FC<RealTimeChartProps> = ({
  symbol,
  title,
  className,
  height = 400,
  maxDataPoints = 100,
  updateInterval = 1000,
  showMetrics = true,
  showControls = true,
  onDataUpdate,
  dataSource,
}) => {
  const [data, setData] = useState<RealTimeDataPoint[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState('1m');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 模拟数据生成器
  const generateMockData = useCallback((): RealTimeDataPoint => {
    const now = Date.now();
    const lastPrice = data.length > 0 ? data[data.length - 1].price : 100;
    const change = (Math.random() - 0.5) * 2; // -1 到 1 的随机变化
    const newPrice = Math.max(0.01, lastPrice + change);
    const priceChange = newPrice - lastPrice;
    const changePercent = lastPrice > 0 ? (priceChange / lastPrice) : 0;
    
    return {
      timestamp: now,
      price: newPrice,
      volume: Math.floor(Math.random() * 10000) + 1000,
      change: priceChange,
      changePercent,
    };
  }, [data]);

  // 数据更新逻辑
  const updateData = useCallback(async () => {
    if (isPaused) return;

    try {
      const newDataPoint = dataSource ? await dataSource() : generateMockData();
      
      setData(prevData => {
        const newData = [...prevData, newDataPoint];
        // 限制数据点数量
        if (newData.length > maxDataPoints) {
          newData.splice(0, newData.length - maxDataPoints);
        }
        
        onDataUpdate?.(newData);
        return newData;
      });
      
      setError(null);
      setIsConnected(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : '数据更新失败');
      setIsConnected(false);
    }
  }, [isPaused, dataSource, generateMockData, maxDataPoints, onDataUpdate]);

  // 初始化和定时更新
  useEffect(() => {
    setLoading(true);
    
    // 初始数据加载
    const initializeData = async () => {
      try {
        // 生成初始历史数据
        const initialData: RealTimeDataPoint[] = [];
        const now = Date.now();
        let price = 100;
        
        for (let i = maxDataPoints - 1; i >= 0; i--) {
          const change = (Math.random() - 0.5) * 2;
          price = Math.max(0.01, price + change);
          const timestamp = now - (i * updateInterval);
          
          initialData.push({
            timestamp,
            price,
            volume: Math.floor(Math.random() * 10000) + 1000,
            change: i === maxDataPoints - 1 ? 0 : change,
            changePercent: i === maxDataPoints - 1 ? 0 : (change / (price - change)),
          });
        }
        
        setData(initialData);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : '初始化失败');
        setLoading(false);
      }
    };

    initializeData();
  }, [maxDataPoints, updateInterval]);

  // 定时更新
  useEffect(() => {
    if (loading || isPaused) return;

    const interval = setInterval(updateData, updateInterval);
    return () => clearInterval(interval);
  }, [loading, isPaused, updateData, updateInterval]);

  // 时间范围配置
  const timeRanges: ChartTimeRange[] = useMemo(() => [
    { label: '1分钟', value: '1m', active: selectedTimeRange === '1m' },
    { label: '5分钟', value: '5m', active: selectedTimeRange === '5m' },
    { label: '15分钟', value: '15m', active: selectedTimeRange === '15m' },
    { label: '1小时', value: '1h', active: selectedTimeRange === '1h' },
  ], [selectedTimeRange]);

  // 过滤数据根据时间范围
  const filteredData = useMemo(() => {
    if (!data.length) return [];
    
    const now = Date.now();
    const timeRangeMs = {
      '1m': 60 * 1000,
      '5m': 5 * 60 * 1000,
      '15m': 15 * 60 * 1000,
      '1h': 60 * 60 * 1000,
    }[selectedTimeRange] || 60 * 1000;
    
    return data.filter(point => now - point.timestamp <= timeRangeMs);
  }, [data, selectedTimeRange]);

  // 计算指标
  const metrics: ChartMetric[] = useMemo(() => {
    if (!data.length) return [];
    
    const latestData = data[data.length - 1];
    const previousData = data.length > 1 ? data[data.length - 2] : null;
    
    return [
      {
        label: '当前价格',
        value: formatCurrency(latestData.price),
        change: latestData.changePercent ? {
          value: latestData.changePercent * 100,
          type: latestData.changePercent > 0 ? 'positive' : latestData.changePercent < 0 ? 'negative' : 'neutral',
        } : undefined,
      },
      {
        label: '成交量',
        value: formatNumber(latestData.volume, 0),
      },
      {
        label: '24h最高',
        value: formatCurrency(Math.max(...data.map(d => d.price))),
      },
      {
        label: '24h最低',
        value: formatCurrency(Math.min(...data.map(d => d.price))),
      },
    ];
  }, [data]);

  const handleTimeRangeChange = useCallback((range: string) => {
    setSelectedTimeRange(range);
  }, []);

  const handlePauseToggle = useCallback(() => {
    setIsPaused(prev => !prev);
  }, []);

  const handleRefresh = useCallback(() => {
    setError(null);
    setIsPaused(false);
    updateData();
  }, [updateData]);

  return (
    <div className={cn('space-y-4', className)}>
      {/* 指标卡片 */}
      {showMetrics && metrics.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {metrics.map((metric, index) => (
            <ChartMetricCard key={index} metric={metric} />
          ))}
        </div>
      )}

      {/* 图表 */}
      <EnhancedLineChart
        data={filteredData.map(point => ({
          timestamp: point.timestamp,
          price: point.price,
          volume: point.volume,
        }))}
        lines={[
          {
            dataKey: 'price',
            name: '价格',
            color: 'hsl(var(--primary))',
            strokeWidth: 2,
          },
        ]}
        title={title || `${symbol} 实时价格`}
        subtitle={`连接状态: ${isConnected ? '已连接' : '未连接'} | 数据点: ${filteredData.length}`}
        height={height}
        loading={loading}
        error={error}
        showRealTimeIndicator={isConnected && !isPaused}
        timeRanges={showControls ? timeRanges : undefined}
        onTimeRangeChange={showControls ? handleTimeRangeChange : undefined}
        xAxisFormatter={(value) => {
          return new Date(value).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          });
        }}
        yAxisFormatter={(value) => formatCurrency(value)}
        tooltipFormatter={(value, name) => [
          formatCurrency(value as number),
          name,
        ]}
        onRefresh={handleRefresh}
        animate={true}
      />

      {/* 控制面板 */}
      {showControls && (
        <div className="flex items-center justify-between p-4 bg-card rounded-lg border">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={cn(
                'h-2 w-2 rounded-full',
                isConnected ? 'bg-success-500 animate-data-point-pulse' : 'bg-muted-foreground'
              )} />
              <span className="text-sm text-muted-foreground">
                {isConnected ? '实时连接' : '连接断开'}
              </span>
            </div>
            <div className="text-sm text-muted-foreground">
              更新间隔: {updateInterval}ms
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={handlePauseToggle}
              className={cn(
                'px-3 py-1 text-sm rounded-md transition-colors',
                isPaused
                  ? 'bg-success-100 text-success-700 hover:bg-success-200'
                  : 'bg-warning-100 text-warning-700 hover:bg-warning-200'
              )}
            >
              {isPaused ? '继续' : '暂停'}
            </button>
            <button
              onClick={handleRefresh}
              className="px-3 py-1 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              刷新
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default RealTimeChart;