'use client';

import React, { useEffect } from 'react';
import Head from 'next/head';

interface SEOProps {
  title?: string;
  description?: string;
  keywords?: string[];
  image?: string;
  url?: string;
  type?: 'website' | 'article' | 'product';
  author?: string;
  publishedTime?: string;
  modifiedTime?: string;
}

export const SEOHead: React.FC<SEOProps> = ({
  title = 'Event Contract Platform',
  description = 'Advanced event-driven contract management and analytics platform',
  keywords = ['event', 'contract', 'analytics', 'blockchain', 'trading'],
  image = '/og-image.jpg',
  url = 'https://event-contract.com',
  type = 'website',
  author = 'Event Contract Team',
  publishedTime,
  modifiedTime,
}) => {
  return (
    <Head>
      {/* Basic Meta Tags */}
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords.join(', ')} />
      <meta name="author" content={author} />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta name="robots" content="index, follow" />
      <meta name="language" content="en" />
      <meta name="revisit-after" content="7 days" />
      
      {/* Open Graph Meta Tags */}
      <meta property="og:type" content={type} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:image" content={image} />
      <meta property="og:url" content={url} />
      <meta property="og:site_name" content="Event Contract Platform" />
      <meta property="og:locale" content="en_US" />
      
      {/* Twitter Card Meta Tags */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={image} />
      <meta name="twitter:creator" content="@eventcontract" />
      
      {/* Article specific meta tags */}
      {type === 'article' && publishedTime && (
        <meta property="article:published_time" content={publishedTime} />
      )}
      {type === 'article' && modifiedTime && (
        <meta property="article:modified_time" content={modifiedTime} />
      )}
      {type === 'article' && author && (
        <meta property="article:author" content={author} />
      )}
      
      {/* Canonical URL */}
      <link rel="canonical" href={url} />
      
      {/* Favicon and Icons */}
      <link rel="icon" href="/favicon.ico" />
      <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
      <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
      <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
      <link rel="manifest" href="/site.webmanifest" />
      
      {/* DNS Prefetch and Preconnect */}
      <link rel="dns-prefetch" href="//fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      
      {/* JSON-LD Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            '@context': 'https://schema.org',
            '@type': type === 'article' ? 'Article' : 'WebSite',
            name: title,
            description: description,
            url: url,
            image: image,
            author: {
              '@type': 'Organization',
              name: author,
            },
            publisher: {
              '@type': 'Organization',
              name: 'Event Contract Platform',
              logo: {
                '@type': 'ImageObject',
                url: '/logo.png',
              },
            },
            ...(publishedTime && { datePublished: publishedTime }),
            ...(modifiedTime && { dateModified: modifiedTime }),
          }),
        }}
      />
    </Head>
  );
};

// Web Vitals optimization component
export const WebVitalsOptimizer: React.FC = () => {
  useEffect(() => {
    // Optimize Largest Contentful Paint (LCP)
    const optimizeLCP = () => {
      // Preload critical resources
      const criticalImages = document.querySelectorAll('img[data-priority="high"]');
      criticalImages.forEach((img) => {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'image';
        link.href = (img as HTMLImageElement).src;
        document.head.appendChild(link);
      });
      
      // Optimize font loading
      const fontLink = document.createElement('link');
      fontLink.rel = 'preload';
      fontLink.as = 'font';
      fontLink.type = 'font/woff2';
      fontLink.crossOrigin = 'anonymous';
      fontLink.href = '/fonts/inter-var.woff2';
      document.head.appendChild(fontLink);
    };
    
    // Optimize First Input Delay (FID)
    const optimizeFID = () => {
      // Break up long tasks
      const scheduler = (callback: () => void) => {
        if ('scheduler' in window && 'postTask' in (window as any).scheduler) {
          (window as any).scheduler.postTask(callback, { priority: 'user-blocking' });
        } else if ('requestIdleCallback' in window) {
          requestIdleCallback(callback);
        } else {
          setTimeout(callback, 0);
        }
      };
      
      // Defer non-critical JavaScript
      const scripts = document.querySelectorAll('script[data-defer="true"]');
      scripts.forEach((script) => {
        scheduler(() => {
          const newScript = document.createElement('script');
          newScript.src = (script as HTMLScriptElement).src;
          newScript.async = true;
          document.head.appendChild(newScript);
        });
      });
    };
    
    // Optimize Cumulative Layout Shift (CLS)
    const optimizeCLS = () => {
      // Add aspect ratio containers for images
      const images = document.querySelectorAll('img:not([width]):not([height])');
      images.forEach((img) => {
        const wrapper = document.createElement('div');
        wrapper.style.aspectRatio = '16 / 9'; // Default aspect ratio
        wrapper.style.overflow = 'hidden';
        img.parentNode?.insertBefore(wrapper, img);
        wrapper.appendChild(img);
      });
      
      // Reserve space for dynamic content
      const dynamicContainers = document.querySelectorAll('[data-dynamic="true"]');
      dynamicContainers.forEach((container) => {
        (container as HTMLElement).style.minHeight = '200px';
      });
    };
    
    // Apply optimizations
    optimizeLCP();
    optimizeFID();
    optimizeCLS();
    
    // Monitor performance
    if ('PerformanceObserver' in window) {
      // Monitor LCP
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        console.log('LCP:', lastEntry.startTime);
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      
      // Monitor FID
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          console.log('FID:', (entry as any).processingStart - entry.startTime);
        });
      });
      fidObserver.observe({ entryTypes: ['first-input'] });
      
      // Monitor CLS
      const clsObserver = new PerformanceObserver((list) => {
        let clsValue = 0;
        const entries = list.getEntries();
        entries.forEach((entry) => {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value;
          }
        });
        console.log('CLS:', clsValue);
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });
    }
  }, []);
  
  return null;
};

// Critical CSS inliner
export const CriticalCSS: React.FC<{ css: string }> = ({ css }) => {
  return (
    <style
      dangerouslySetInnerHTML={{
        __html: css,
      }}
    />
  );
};

// Resource hints component
export const ResourceHints: React.FC = () => {
  return (
    <Head>
      {/* DNS Prefetch */}
      <link rel="dns-prefetch" href="//fonts.googleapis.com" />
      <link rel="dns-prefetch" href="//api.example.com" />
      
      {/* Preconnect */}
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      
      {/* Preload critical resources */}
      <link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
      <link rel="preload" href="/critical.css" as="style" />
      
      {/* Prefetch next page resources */}
      <link rel="prefetch" href="/dashboard" />
      <link rel="prefetch" href="/analytics" />
    </Head>
  );
};

// Service Worker registration
export const ServiceWorkerRegistration: React.FC = () => {
  useEffect(() => {
    if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
      navigator.serviceWorker
        .register('/sw.js')
        .then((registration) => {
          console.log('SW registered: ', registration);
        })
        .catch((registrationError) => {
          console.log('SW registration failed: ', registrationError);
        });
    }
  }, []);
  
  return null;
};

// Image optimization component
interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  priority?: boolean;
  className?: string;
  sizes?: string;
}

export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  width,
  height,
  priority = false,
  className = '',
  sizes = '(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw',
}) => {
  const [isLoaded, setIsLoaded] = React.useState(false);
  const [hasError, setHasError] = React.useState(false);
  
  return (
    <div
      className={`relative overflow-hidden ${className}`}
      style={{
        aspectRatio: width && height ? `${width} / ${height}` : undefined,
      }}
    >
      <img
        src={src}
        alt={alt}
        width={width}
        height={height}
        loading={priority ? 'eager' : 'lazy'}
        decoding="async"
        sizes={sizes}
        className={`
          transition-opacity duration-300
          ${isLoaded ? 'opacity-100' : 'opacity-0'}
          ${hasError ? 'hidden' : ''}
        `}
        onLoad={() => setIsLoaded(true)}
        onError={() => setHasError(true)}
        data-priority={priority ? 'high' : 'normal'}
      />
      
      {/* Loading placeholder */}
      {!isLoaded && !hasError && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse" />
      )}
      
      {/* Error fallback */}
      {hasError && (
        <div className="absolute inset-0 bg-gray-100 flex items-center justify-center">
          <span className="text-gray-500 text-sm">Image failed to load</span>
        </div>
      )}
    </div>
  );
};

// Analytics and tracking
export const Analytics: React.FC = () => {
  useEffect(() => {
    // Google Analytics 4
    if (process.env.NEXT_PUBLIC_GA_ID) {
      const script = document.createElement('script');
      script.src = `https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GA_ID}`;
      script.async = true;
      document.head.appendChild(script);
      
      (window as any).dataLayer = (window as any).dataLayer || [];
      const gtag = (...args: any[]) => {
        (window as any).dataLayer.push(args);
      };
      gtag('js', new Date());
      gtag('config', process.env.NEXT_PUBLIC_GA_ID, {
        page_title: document.title,
        page_location: window.location.href,
      });
    }
    
    // Performance tracking
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry) => {
          // Send performance data to analytics
          if ((window as any).gtag) {
            (window as any).gtag('event', 'performance_metric', {
              metric_name: entry.entryType,
              metric_value: entry.duration || entry.startTime,
              custom_parameter: entry.name,
            });
          }
        });
      });
      
      observer.observe({ entryTypes: ['navigation', 'paint', 'largest-contentful-paint'] });
    }
  }, []);
  
  return null;
};