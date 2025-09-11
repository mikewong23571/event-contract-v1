'use client';

import { useEffect } from 'react';
import { onCLS, onINP, onFCP, onLCP, onTTFB } from 'web-vitals';
import { usePerformanceStore } from '../../stores/performanceStore';

interface WebVitalsMetric {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  id: string;
}

interface WebVitalsMonitorProps {
  reportWebVitals?: (metric: WebVitalsMetric) => void;
  enableConsoleLogging?: boolean;
}

const WebVitalsMonitor: React.FC<WebVitalsMonitorProps> = ({
  reportWebVitals,
  enableConsoleLogging = false,
}) => {
  const recordPageLoad = usePerformanceStore((state) => state.recordPageLoad);
  const recordError = usePerformanceStore((state) => state.recordError);
  const updateMemoryUsage = usePerformanceStore((state) => state.updateMemoryUsage);

  useEffect(() => {
    // Monitor Core Web Vitals
    const handleMetric = (metric: WebVitalsMetric) => {
      if (enableConsoleLogging) {
        console.log(`[Web Vitals] ${metric.name}:`, metric.value, metric.rating);
      }

      // Store metrics in performance store
      switch (metric.name) {
        case 'LCP':
        case 'FCP':
        case 'TTFB':
          recordPageLoad(metric.value);
          break;
        default:
          break;
      }

      // Call custom reporter if provided
      if (reportWebVitals) {
        reportWebVitals(metric);
      }

      // Send to analytics (example)
      if (typeof window !== 'undefined' && (window as any).gtag) {
        (window as any).gtag('event', metric.name, {
          event_category: 'Web Vitals',
          value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
          event_label: metric.id,
          non_interaction: true,
        });
      }
    };

    // Initialize Web Vitals monitoring
    onCLS(handleMetric);
    onINP(handleMetric); // INP replaced FID in web-vitals v4+
    onFCP(handleMetric);
    onLCP(handleMetric);
    onTTFB(handleMetric);

    // Monitor memory usage periodically
    const memoryInterval = setInterval(() => {
      updateMemoryUsage();
    }, 30000); // Every 30 seconds

    // Monitor for JavaScript errors
    const handleError = (event: ErrorEvent) => {
      recordError();
      if (enableConsoleLogging) {
        console.error('[Performance Monitor] JavaScript Error:', event.error);
      }
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      recordError();
      if (enableConsoleLogging) {
        console.error('[Performance Monitor] Unhandled Promise Rejection:', event.reason);
      }
    };

    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    // Performance observer for additional metrics
    if ('PerformanceObserver' in window) {
      try {
        // Monitor long tasks
        const longTaskObserver = new PerformanceObserver((list) => {
          list.getEntries().forEach((entry) => {
            if (entry.duration > 50) { // Tasks longer than 50ms
              if (enableConsoleLogging) {
                console.warn(`[Performance Monitor] Long Task detected: ${entry.duration}ms`);
              }
            }
          });
        });
        longTaskObserver.observe({ entryTypes: ['longtask'] });

        // Monitor layout shifts
        const layoutShiftObserver = new PerformanceObserver((list) => {
          list.getEntries().forEach((entry: any) => {
            if (entry.hadRecentInput) return; // Ignore shifts caused by user input
            
            if (entry.value > 0.1) { // Significant layout shift
              if (enableConsoleLogging) {
                console.warn(`[Performance Monitor] Layout Shift detected: ${entry.value}`);
              }
            }
          });
        });
        layoutShiftObserver.observe({ entryTypes: ['layout-shift'] });

        // Monitor resource loading
        const resourceObserver = new PerformanceObserver((list) => {
          list.getEntries().forEach((entry) => {
            const resource = entry as PerformanceResourceTiming;
            const loadTime = resource.responseEnd - resource.requestStart;
            
            if (loadTime > 1000) { // Resources taking longer than 1s
              if (enableConsoleLogging) {
                console.warn(`[Performance Monitor] Slow Resource: ${resource.name} (${loadTime}ms)`);
              }
            }
          });
        });
        resourceObserver.observe({ entryTypes: ['resource'] });
      } catch (error) {
        console.warn('[Performance Monitor] PerformanceObserver not fully supported:', error);
      }
    }

    return () => {
      clearInterval(memoryInterval);
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, [recordPageLoad, recordError, updateMemoryUsage, reportWebVitals, enableConsoleLogging]);

  return null; // This is a monitoring component, no UI
};

export default WebVitalsMonitor;

// Utility function to get performance insights
export const getPerformanceInsights = () => {
  if (typeof window === 'undefined') return null;

  const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
  const paint = performance.getEntriesByType('paint');
  
  const insights = {
    // Navigation timing
    domContentLoaded: navigation?.domContentLoadedEventEnd - navigation?.domContentLoadedEventStart,
    loadComplete: navigation?.loadEventEnd - navigation?.loadEventStart,
    
    // Paint timing
    firstPaint: paint.find(entry => entry.name === 'first-paint')?.startTime || 0,
    firstContentfulPaint: paint.find(entry => entry.name === 'first-contentful-paint')?.startTime || 0,
    
    // Memory info (Chrome only)
    memoryUsage: (performance as any).memory ? {
      used: Math.round((performance as any).memory.usedJSHeapSize / 1024 / 1024),
      total: Math.round((performance as any).memory.totalJSHeapSize / 1024 / 1024),
      limit: Math.round((performance as any).memory.jsHeapSizeLimit / 1024 / 1024),
    } : null,
    
    // Connection info
    connection: (navigator as any).connection ? {
      effectiveType: (navigator as any).connection.effectiveType,
      downlink: (navigator as any).connection.downlink,
      rtt: (navigator as any).connection.rtt,
    } : null,
  };
  
  return insights;
};

// Performance budget checker
export const checkPerformanceBudget = () => {
  const insights = getPerformanceInsights();
  if (!insights) return null;
  
  const budget = {
    firstContentfulPaint: 1500, // 1.5s
    domContentLoaded: 2000, // 2s
    loadComplete: 3000, // 3s
    memoryUsage: 50, // 50MB
  };
  
  const violations = [];
  
  if (insights.firstContentfulPaint > budget.firstContentfulPaint) {
    violations.push(`First Contentful Paint: ${insights.firstContentfulPaint}ms (budget: ${budget.firstContentfulPaint}ms)`);
  }
  
  if (insights.domContentLoaded > budget.domContentLoaded) {
    violations.push(`DOM Content Loaded: ${insights.domContentLoaded}ms (budget: ${budget.domContentLoaded}ms)`);
  }
  
  if (insights.loadComplete > budget.loadComplete) {
    violations.push(`Load Complete: ${insights.loadComplete}ms (budget: ${budget.loadComplete}ms)`);
  }
  
  if (insights.memoryUsage && insights.memoryUsage.used > budget.memoryUsage) {
    violations.push(`Memory Usage: ${insights.memoryUsage.used}MB (budget: ${budget.memoryUsage}MB)`);
  }
  
  return {
    passed: violations.length === 0,
    violations,
    insights,
  };
};