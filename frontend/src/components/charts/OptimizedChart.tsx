'use client';

import React, { memo, useMemo, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRenderTimeTracker } from '../../stores/performanceStore';
import { cn } from '@/lib/utils';

export interface OptimizedChartProps {
  data: any[];
  className?: string;
  title?: string;
  subtitle?: string;
  loading?: boolean;
  error?: string | null;
  height?: number;
  width?: number;
  children?: React.ReactNode;
  onRefresh?: () => void;
  enableVirtualization?: boolean;
  maxDataPoints?: number;
  updateInterval?: number;
}

// Memoized loading component
const ChartLoading = memo(() => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    className="flex flex-col items-center justify-center h-full space-y-4"
  >
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full"
    />
    <p className="text-sm text-muted-foreground">加载图表数据...</p>
  </motion.div>
));

ChartLoading.displayName = 'ChartLoading';

// Memoized error component
const ChartError = memo<{ error: string; onRefresh?: () => void }>(({ error, onRefresh }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className="flex flex-col items-center justify-center h-full space-y-4 p-6"
  >
    <div className="w-12 h-12 rounded-full bg-destructive/10 flex items-center justify-center">
      <svg className="w-6 h-6 text-destructive" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
    </div>
    <div className="text-center space-y-2">
      <p className="text-sm font-medium text-destructive">图表加载失败</p>
      <p className="text-xs text-muted-foreground max-w-xs">{error}</p>
    </div>
    {onRefresh && (
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onRefresh}
        className="px-4 py-2 text-xs bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
      >
        重新加载
      </motion.button>
    )}
  </motion.div>
));

ChartError.displayName = 'ChartError';

// Memoized header component
const ChartHeader = memo<{ title?: string; subtitle?: string }>(({ title, subtitle }) => {
  if (!title && !subtitle) return null;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-4 space-y-1"
    >
      {title && (
        <h3 className="text-lg font-semibold text-foreground">{title}</h3>
      )}
      {subtitle && (
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      )}
    </motion.div>
  );
});

ChartHeader.displayName = 'ChartHeader';

// Data virtualization hook
const useDataVirtualization = (data: any[], maxDataPoints: number = 1000) => {
  return useMemo(() => {
    if (!data || data.length <= maxDataPoints) {
      return data;
    }
    
    // Sample data points evenly
    const step = Math.ceil(data.length / maxDataPoints);
    return data.filter((_, index) => index % step === 0);
  }, [data, maxDataPoints]);
};

// Performance monitoring hook
const useChartPerformance = (componentName: string) => {
  useRenderTimeTracker(componentName);
  const renderCountRef = useRef(0);
  
  useEffect(() => {
    renderCountRef.current += 1;
  });
  
  return renderCountRef.current;
};

// Main optimized chart component
const OptimizedChart: React.FC<OptimizedChartProps> = memo(({
  data,
  className,
  title,
  subtitle,
  loading = false,
  error = null,
  height = 400,
  width,
  children,
  onRefresh,
  enableVirtualization = true,
  maxDataPoints = 1000,
  updateInterval = 1000,
}) => {
  const renderCount = useChartPerformance('OptimizedChart');
  
  // Virtualize data if enabled
  const virtualizedData = useDataVirtualization(
    enableVirtualization ? data : data,
    maxDataPoints
  );
  
  // Memoize container styles
  const containerStyle = useMemo(() => ({
    height: `${height}px`,
    width: width ? `${width}px` : '100%',
  }), [height, width]);
  
  // Memoize refresh handler
  const handleRefresh = useCallback(() => {
    onRefresh?.();
  }, [onRefresh]);
  
  // Memoize data status
  const dataStatus = useMemo(() => {
    if (loading) return 'loading';
    if (error) return 'error';
    if (!virtualizedData || virtualizedData.length === 0) return 'empty';
    return 'ready';
  }, [loading, error, virtualizedData]);
  
  return (
    <div 
      className={cn(
        'relative bg-card rounded-lg border p-4 transition-all duration-200',
        'hover:shadow-md',
        className
      )} 
      style={containerStyle}
    >
      <ChartHeader title={title} subtitle={subtitle} />
      
      <AnimatePresence mode="wait">
        {dataStatus === 'loading' && (
          <motion.div key="loading" className="absolute inset-4 flex items-center justify-center">
            <ChartLoading />
          </motion.div>
        )}
        
        {dataStatus === 'error' && (
          <motion.div key="error" className="absolute inset-4 flex items-center justify-center">
            <ChartError error={error!} onRefresh={handleRefresh} />
          </motion.div>
        )}
        
        {dataStatus === 'empty' && (
          <motion.div 
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-4 flex items-center justify-center"
          >
            <div className="text-center space-y-2">
              <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mx-auto">
                <svg className="w-6 h-6 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <p className="text-sm text-muted-foreground">暂无数据</p>
            </div>
          </motion.div>
        )}
        
        {dataStatus === 'ready' && (
          <motion.div
            key="chart"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="h-full"
          >
            {children}
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Performance debug info (development only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="absolute top-2 right-2 text-xs text-muted-foreground bg-muted/50 px-2 py-1 rounded">
          Renders: {renderCount} | Points: {virtualizedData?.length || 0}
        </div>
      )}
    </div>
  );
});

OptimizedChart.displayName = 'OptimizedChart';

export default OptimizedChart;

// Export utility functions for chart optimization
export const chartOptimizationUtils = {
  // Debounce function for chart updates
  debounce: <T extends (...args: any[]) => any>(func: T, wait: number) => {
    let timeout: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(...args), wait);
    };
  },
  
  // Throttle function for real-time updates
  throttle: <T extends (...args: any[]) => any>(func: T, limit: number) => {
    let inThrottle: boolean;
    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func(...args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },
  
  // Data sampling for large datasets
  sampleData: (data: any[], maxPoints: number) => {
    if (data.length <= maxPoints) return data;
    const step = Math.ceil(data.length / maxPoints);
    return data.filter((_, index) => index % step === 0);
  },
};