'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { useState } from 'react';
import WebVitalsMonitor from '@/components/performance/WebVitalsMonitor';
import { MobileOptimizations } from '@/components/mobile/MobileOptimizations';
import { WebVitalsOptimizer, ResourceHints, ServiceWorkerRegistration, Analytics } from '@/components/seo/SEOOptimizations';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 60 * 5,
            refetchOnWindowFocus: false,
            retry: (failureCount, error: any) => {
              if (error?.status >= 400 && error?.status < 500) {
                return false;
              }
              return failureCount < 3;
            },
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <ResourceHints />
      <MobileOptimizations />
      <WebVitalsOptimizer />
      <ServiceWorkerRegistration />
      <Analytics />
      <WebVitalsMonitor enableConsoleLogging={process.env.NODE_ENV === 'development'} />
      {children}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'hsl(var(--card))',
            color: 'hsl(var(--card-foreground))',
            border: '1px solid hsl(var(--border))',
          },
        }}
      />
    </QueryClientProvider>
  );
}