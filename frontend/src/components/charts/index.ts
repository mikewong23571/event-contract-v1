// 基础图表组件
export { default as BaseChart } from './BaseChart';
export type { BaseChartProps, ChartMetric, ChartTimeRange } from './BaseChart';
export { ChartMetricCard, ChartTimeSelector } from './BaseChart';

// 增强的线性图表
export { default as EnhancedLineChart } from './EnhancedLineChart';
export type { LineChartDataPoint, LineConfig, EnhancedLineChartProps } from './EnhancedLineChart';
export { presetConfigs as lineChartPresets } from './EnhancedLineChart';

// 增强的面积图表
export { default as EnhancedAreaChart } from './EnhancedAreaChart';
export type { AreaChartDataPoint, AreaConfig, EnhancedAreaChartProps } from './EnhancedAreaChart';
export { presetConfigs as areaChartPresets } from './EnhancedAreaChart';

// 增强的柱状图表
export { default as EnhancedBarChart } from './EnhancedBarChart';
export type { BarChartDataPoint, BarConfig, EnhancedBarChartProps } from './EnhancedBarChart';
export { presetConfigs as barChartPresets } from './EnhancedBarChart';

// 实时图表
export { default as RealTimeChart } from './RealTimeChart';
export type { RealTimeDataPoint, RealTimeChartProps } from './RealTimeChart';

// 原有的市场数据图表（保持向后兼容）
export { default as MarketDataChart } from './MarketDataChart';

// 图表工具函数
export const chartUtils = {
  // 生成时间序列数据
  generateTimeSeriesData: (count: number, startTime?: number) => {
    const start = startTime || Date.now() - (count * 60 * 1000);
    return Array.from({ length: count }, (_, i) => ({
      timestamp: start + (i * 60 * 1000),
      value: Math.random() * 100 + 50,
    }));
  },

  // 生成随机颜色
  generateColors: (count: number) => {
    const colors = [
      'hsl(var(--primary))',
      'hsl(var(--secondary))',
      'hsl(var(--accent))',
      'hsl(var(--success))',
      'hsl(var(--warning))',
      'hsl(var(--destructive))',
    ];
    
    if (count <= colors.length) {
      return colors.slice(0, count);
    }
    
    // 生成更多颜色
    const additionalColors = [];
    for (let i = colors.length; i < count; i++) {
      const hue = (i * 137.508) % 360; // 黄金角度分布
      additionalColors.push(`hsl(${hue}, 70%, 50%)`);
    }
    
    return [...colors, ...additionalColors];
  },

  // 数据聚合函数
  aggregateData: (data: any[], groupBy: 'hour' | 'day' | 'week' | 'month', valueKey: string) => {
    const grouped = new Map();
    
    data.forEach(item => {
      const date = new Date(item.timestamp);
      let key: string;
      
      switch (groupBy) {
        case 'hour':
          key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}-${date.getHours()}`;
          break;
        case 'day':
          key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
          break;
        case 'week':
          const weekStart = new Date(date);
          weekStart.setDate(date.getDate() - date.getDay());
          key = `${weekStart.getFullYear()}-${weekStart.getMonth()}-${weekStart.getDate()}`;
          break;
        case 'month':
          key = `${date.getFullYear()}-${date.getMonth()}`;
          break;
        default:
          key = item.timestamp.toString();
      }
      
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key).push(item);
    });
    
    return Array.from(grouped.entries()).map(([key, items]) => {
      const values = items.map((item: any) => item[valueKey]).filter((v: any) => typeof v === 'number');
      return {
        timestamp: items[0].timestamp,
        [valueKey]: values.reduce((sum: number, val: number) => sum + val, 0) / values.length,
        count: items.length,
      };
    }).sort((a, b) => a.timestamp - b.timestamp);
  },

  // 计算移动平均线
  calculateMovingAverage: (data: any[], valueKey: string, window: number) => {
    return data.map((item, index) => {
      const start = Math.max(0, index - window + 1);
      const slice = data.slice(start, index + 1);
      const average = slice.reduce((sum, d) => sum + (d[valueKey] || 0), 0) / slice.length;
      
      return {
        ...item,
        [`${valueKey}_ma${window}`]: average,
      };
    });
  },

  // 计算百分比变化
  calculatePercentageChange: (data: any[], valueKey: string) => {
    return data.map((item, index) => {
      if (index === 0) {
        return { ...item, [`${valueKey}_change`]: 0 };
      }
      
      const current = item[valueKey] || 0;
      const previous = data[index - 1][valueKey] || 0;
      const change = previous !== 0 ? ((current - previous) / previous) * 100 : 0;
      
      return {
        ...item,
        [`${valueKey}_change`]: change,
      };
    });
  },
};

// 图表主题配置
export const chartThemes = {
  default: {
    colors: {
      primary: 'hsl(var(--primary))',
      secondary: 'hsl(var(--secondary))',
      accent: 'hsl(var(--accent))',
      success: 'hsl(var(--success))',
      warning: 'hsl(var(--warning))',
      destructive: 'hsl(var(--destructive))',
    },
    grid: {
      stroke: 'hsl(var(--border))',
      strokeDasharray: '3 3',
    },
    axis: {
      stroke: 'hsl(var(--muted-foreground))',
      fontSize: 12,
    },
  },
  dark: {
    colors: {
      primary: 'hsl(var(--primary))',
      secondary: 'hsl(var(--secondary))',
      accent: 'hsl(var(--accent))',
      success: '#10b981',
      warning: '#f59e0b',
      destructive: '#ef4444',
    },
    grid: {
      stroke: 'hsl(var(--border))',
      strokeDasharray: '3 3',
    },
    axis: {
      stroke: 'hsl(var(--muted-foreground))',
      fontSize: 12,
    },
  },
};

// 常用图表配置
export const commonChartConfigs = {
  // 时间轴格式化器
  timeFormatters: {
    minute: (timestamp: number) => new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    }),
    hour: (timestamp: number) => new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    }),
    day: (timestamp: number) => new Date(timestamp).toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
    }),
    week: (timestamp: number) => new Date(timestamp).toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
    }),
    month: (timestamp: number) => new Date(timestamp).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
    }),
  },

  // 数值格式化器
  valueFormatters: {
    currency: (value: number) => new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
    }).format(value),
    percentage: (value: number) => `${(value * 100).toFixed(2)}%`,
    number: (value: number, decimals: number = 2) => new Intl.NumberFormat('zh-CN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value),
    compact: (value: number) => new Intl.NumberFormat('zh-CN', {
      notation: 'compact',
      compactDisplay: 'short',
    }).format(value),
  },

  // 默认时间范围
  defaultTimeRanges: [
    { label: '1分钟', value: '1m' },
    { label: '5分钟', value: '5m' },
    { label: '15分钟', value: '15m' },
    { label: '1小时', value: '1h' },
    { label: '4小时', value: '4h' },
    { label: '1天', value: '1d' },
    { label: '1周', value: '1w' },
    { label: '1月', value: '1M' },
  ],
};