'use client';

import { useEffect } from 'react';
import { onCLS, onINP, onFCP, onLCP, onTTFB, Metric } from 'web-vitals';

interface WebVitalsProps {
  onMetric?: (metric: Metric) => void;
  debug?: boolean;
}

export function WebVitals({ onMetric, debug = false }: WebVitalsProps) {
  useEffect(() => {
    const handleMetric = (metric: Metric) => {
      if (debug) {
        console.log(`[Web Vitals] ${metric.name}:`, metric.value, metric);
      }
      
      // Send to analytics service
      if (typeof window !== 'undefined' && 'gtag' in window) {
        (window as any).gtag('event', metric.name, {
          event_category: 'Web Vitals',
          value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
          event_label: metric.id,
          non_interaction: true,
        });
      }
      
      // Custom callback
      onMetric?.(metric);
    };

    // Measure Core Web Vitals
    onCLS(handleMetric);
    onINP(handleMetric);
    onFCP(handleMetric);
    onLCP(handleMetric);
    onTTFB(handleMetric);
  }, [onMetric, debug]);

  return null;
}

// Performance monitoring hook
export function useWebVitals(debug = false) {
  useEffect(() => {
    const metrics: Record<string, number> = {};
    
    const handleMetric = (metric: Metric) => {
      metrics[metric.name] = metric.value;
      
      if (debug) {
        console.table(metrics);
      }
    };

    onCLS(handleMetric);
    onINP(handleMetric);
    onFCP(handleMetric);
    onLCP(handleMetric);
    onTTFB(handleMetric);
  }, [debug]);
}

// Performance observer for custom metrics
export class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: Map<string, number[]> = new Map();
  private observers: PerformanceObserver[] = [];

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  startMonitoring() {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) {
      return;
    }

    // Monitor navigation timing
    const navObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'navigation') {
          const navEntry = entry as PerformanceNavigationTiming;
          this.recordMetric('domContentLoaded', navEntry.domContentLoadedEventEnd - navEntry.domContentLoadedEventStart);
          this.recordMetric('loadComplete', navEntry.loadEventEnd - navEntry.loadEventStart);
        }
      }
    });
    navObserver.observe({ entryTypes: ['navigation'] });
    this.observers.push(navObserver);

    // Monitor resource loading
    const resourceObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'resource') {
          const resourceEntry = entry as PerformanceResourceTiming;
          this.recordMetric(`resource_${resourceEntry.initiatorType}`, resourceEntry.duration);
        }
      }
    });
    resourceObserver.observe({ entryTypes: ['resource'] });
    this.observers.push(resourceObserver);

    // Monitor long tasks
    const longTaskObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'longtask') {
          this.recordMetric('longTask', entry.duration);
        }
      }
    });
    longTaskObserver.observe({ entryTypes: ['longtask'] });
    this.observers.push(longTaskObserver);
  }

  recordMetric(name: string, value: number) {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }
    this.metrics.get(name)!.push(value);
  }

  getMetrics() {
    const result: Record<string, { avg: number; min: number; max: number; count: number }> = {};
    
    for (const [name, values] of Array.from(this.metrics.entries())) {
      result[name] = {
        avg: values.reduce((a: number, b: number) => a + b, 0) / values.length,
        min: Math.min(...values),
        max: Math.max(...values),
        count: values.length,
      };
    }
    
    return result;
  }

  clearMetrics() {
    this.metrics.clear();
  }

  stopMonitoring() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// React component for performance debugging
export function PerformanceDebugger({ enabled = false }: { enabled?: boolean }) {
  useEffect(() => {
    if (!enabled) return;

    const monitor = PerformanceMonitor.getInstance();
    monitor.startMonitoring();

    const interval = setInterval(() => {
      console.log('[Performance Metrics]', monitor.getMetrics());
    }, 10000); // Log every 10 seconds

    return () => {
      clearInterval(interval);
      monitor.stopMonitoring();
    };
  }, [enabled]);

  return null;
}