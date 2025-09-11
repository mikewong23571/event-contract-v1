'use client';

import React, { lazy, Suspense, ComponentType } from 'react';
import { motion } from 'framer-motion';

// Loading component with animation
const LoadingFallback = ({ message = 'Loading...' }: { message?: string }) => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="flex flex-col items-center justify-center p-8 space-y-4"
  >
    <div className="loading-spinner h-8 w-8" />
    <p className="text-sm text-muted-foreground">{message}</p>
  </motion.div>
);

// Chart Loading Fallback
const ChartLoadingFallback = () => (
  <div className="w-full h-64 bg-muted/20 rounded-lg animate-pulse flex items-center justify-center">
    <div className="text-center space-y-2">
      <div className="loading-spinner h-6 w-6 mx-auto" />
      <p className="text-sm text-muted-foreground">Loading chart...</p>
    </div>
  </div>
);

// Lazy loaded components
export const LazyMarketDataChart = lazy(() => import('@/components/charts/MarketDataChart'));
export const LazyBacktestResults = lazy(() => import('@/components/backtesting/BacktestResults'));
export const LazyRealTimeChart = lazy(() => import('@/components/charts/RealTimeChart'));
export const LazyEnhancedAreaChart = lazy(() => import('@/components/charts/EnhancedAreaChart'));
export const LazyEnhancedBarChart = lazy(() => import('@/components/charts/EnhancedBarChart'));
export const LazyEnhancedLineChart = lazy(() => import('@/components/charts/EnhancedLineChart'));
export const LazyRiskParameters = lazy(() => import('@/components/risk/RiskParameters'));

// HOC for wrapping lazy components with Suspense
export function withLazyLoading<T extends object>(
  LazyComponent: ComponentType<T>,
  fallback?: React.ReactNode,
  errorBoundary?: boolean
) {
  return function WrappedComponent(props: T) {
    const defaultFallback = fallback || <LoadingFallback />;
    
    if (errorBoundary) {
      return (
        <ErrorBoundary>
          <Suspense fallback={defaultFallback}>
            <LazyComponent {...props} />
          </Suspense>
        </ErrorBoundary>
      );
    }
    
    return (
      <Suspense fallback={defaultFallback}>
        <LazyComponent {...props} />
      </Suspense>
    );
  };
}

// Error Boundary Component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Lazy component error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 border border-destructive/20 rounded-lg bg-destructive/5">
          <h3 className="text-sm font-medium text-destructive mb-2">Failed to load component</h3>
          <p className="text-xs text-muted-foreground">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: undefined })}
            className="mt-2 text-xs text-primary hover:underline"
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Pre-configured lazy components with appropriate fallbacks
export const LazyMarketDataChartWithFallback = withLazyLoading(
  LazyMarketDataChart,
  <ChartLoadingFallback />,
  true
);

export const LazyBacktestResultsWithFallback = withLazyLoading(
  LazyBacktestResults,
  <LoadingFallback message="Loading backtest results..." />,
  true
);

export const LazyRealTimeChartWithFallback = withLazyLoading(
  LazyRealTimeChart,
  <ChartLoadingFallback />,
  true
);

export const LazyRiskParametersWithFallback = withLazyLoading(
  LazyRiskParameters,
  <LoadingFallback message="Loading risk parameters..." />,
  true
);

// Export all lazy components
export {
  LoadingFallback,
  ChartLoadingFallback,
};