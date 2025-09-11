import React from 'react';
import { create } from 'zustand';

interface PerformanceMetrics {
  pageLoadTime: number;
  componentRenderTime: Record<string, number>;
  apiResponseTimes: Record<string, number[]>;
  memoryUsage: number;
  errorCount: number;
  userInteractions: number;
}

interface PerformanceState {
  metrics: PerformanceMetrics;
  isMonitoring: boolean;
  
  startMonitoring: () => void;
  stopMonitoring: () => void;
  recordPageLoad: (time: number) => void;
  recordComponentRender: (componentName: string, time: number) => void;
  recordApiResponse: (endpoint: string, time: number) => void;
  recordError: () => void;
  recordUserInteraction: () => void;
  updateMemoryUsage: () => void;
  getAverageApiTime: (endpoint: string) => number;
  resetMetrics: () => void;
}

const initialMetrics: PerformanceMetrics = {
  pageLoadTime: 0,
  componentRenderTime: {},
  apiResponseTimes: {},
  memoryUsage: 0,
  errorCount: 0,
  userInteractions: 0,
};

export const usePerformanceStore = create<PerformanceState>((set, get) => ({
  metrics: initialMetrics,
  isMonitoring: false,

  startMonitoring: () => set({ isMonitoring: true }),
  stopMonitoring: () => set({ isMonitoring: false }),

  recordPageLoad: (time: number) => {
    set((state) => ({
      metrics: { ...state.metrics, pageLoadTime: time },
    }));
  },

  recordComponentRender: (componentName: string, time: number) => {
    set((state) => ({
      metrics: {
        ...state.metrics,
        componentRenderTime: {
          ...state.metrics.componentRenderTime,
          [componentName]: time,
        },
      },
    }));
  },

  recordApiResponse: (endpoint: string, time: number) => {
    set((state) => {
      const existingTimes = state.metrics.apiResponseTimes[endpoint] || [];
      const updatedTimes = [...existingTimes, time].slice(-10);
      
      return {
        metrics: {
          ...state.metrics,
          apiResponseTimes: {
            ...state.metrics.apiResponseTimes,
            [endpoint]: updatedTimes,
          },
        },
      };
    });
  },

  recordError: () => {
    set((state) => ({
      metrics: {
        ...state.metrics,
        errorCount: state.metrics.errorCount + 1,
      },
    }));
  },

  recordUserInteraction: () => {
    set((state) => ({
      metrics: {
        ...state.metrics,
        userInteractions: state.metrics.userInteractions + 1,
      },
    }));
  },

  updateMemoryUsage: () => {
    if (typeof window !== 'undefined' && 'performance' in window) {
      const memory = (window.performance as any).memory;
      if (memory) {
        const usageInMB = memory.usedJSHeapSize / 1024 / 1024;
        set((state) => ({
          metrics: {
            ...state.metrics,
            memoryUsage: Math.round(usageInMB * 100) / 100,
          },
        }));
      }
    }
  },

  getAverageApiTime: (endpoint: string) => {
    const times = get().metrics.apiResponseTimes[endpoint] || [];
    if (times.length === 0) return 0;
    return times.reduce((sum: number, time: number) => sum + time, 0) / times.length;
  },

  resetMetrics: () => set({ metrics: initialMetrics }),
}));

// Performance hooks
export const useRenderTimeTracker = (componentName: string) => {
  const recordComponentRender = usePerformanceStore((state) => state.recordComponentRender);
  
  React.useEffect(() => {
    const startTime = performance.now();
    return () => {
      const endTime = performance.now();
      recordComponentRender(componentName, endTime - startTime);
    };
  }, [componentName, recordComponentRender]);
};

export const useApiTracker = () => {
  const recordApiResponse = usePerformanceStore((state) => state.recordApiResponse);
  const recordError = usePerformanceStore((state) => state.recordError);
  
  const trackApiCall = async <T>(
    endpoint: string,
    apiCall: () => Promise<T>
  ): Promise<T> => {
    const startTime = performance.now();
    try {
      const result = await apiCall();
      const endTime = performance.now();
      recordApiResponse(endpoint, endTime - startTime);
      return result;
    } catch (error) {
      recordError();
      throw error;
    }
  };
  
  return { trackApiCall };
};