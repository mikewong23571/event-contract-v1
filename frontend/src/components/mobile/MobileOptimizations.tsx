'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useMediaQuery } from '@/hooks/use-media-query';

// Mobile-specific optimizations
export const MobileOptimizations: React.FC = () => {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const [isLowEndDevice, setIsLowEndDevice] = useState(false);
  const [networkSpeed, setNetworkSpeed] = useState<'slow' | 'fast' | 'unknown'>('unknown');

  useEffect(() => {
    // Detect low-end devices
    const detectLowEndDevice = () => {
      if (typeof window === 'undefined') return false;
      
      const memory = (navigator as any).deviceMemory;
      const cores = navigator.hardwareConcurrency;
      
      // Consider device low-end if:
      // - Less than 4GB RAM or unknown
      // - Less than 4 CPU cores or unknown
      return (memory && memory < 4) || (cores && cores < 4) || (!memory && !cores);
    };

    // Detect network speed
    const detectNetworkSpeed = () => {
      const connection = (navigator as any).connection;
      if (!connection) return 'unknown';
      
      const effectiveType = connection.effectiveType;
      return effectiveType === '4g' ? 'fast' : 'slow';
    };

    setIsLowEndDevice(detectLowEndDevice());
    setNetworkSpeed(detectNetworkSpeed());

    // Apply mobile-specific optimizations
    if (isMobile) {
      // Disable hover effects on mobile
      document.documentElement.classList.add('mobile-device');
      
      // Optimize scroll performance
      (document.body.style as any).webkitOverflowScrolling = 'touch';
      
      // Prevent zoom on input focus
      const viewport = document.querySelector('meta[name=viewport]');
      if (viewport) {
        viewport.setAttribute('content', 
          'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'
        );
      }
    }

    return () => {
      if (isMobile) {
        document.documentElement.classList.remove('mobile-device');
      }
    };
  }, [isMobile]);

  // Reduce animations for low-end devices
  useEffect(() => {
    if (isLowEndDevice) {
      document.documentElement.classList.add('reduce-motion');
    }
    
    return () => {
      document.documentElement.classList.remove('reduce-motion');
    };
  }, [isLowEndDevice]);

  return null;
};

// Touch-optimized button component
interface TouchButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const TouchButton: React.FC<TouchButtonProps> = ({
  children,
  onClick,
  className = '',
  disabled = false,
  size = 'md',
}) => {
  const [isPressed, setIsPressed] = useState(false);
  
  const sizeClasses = {
    sm: 'min-h-[40px] px-3 py-2 text-sm',
    md: 'min-h-[44px] px-4 py-3 text-base',
    lg: 'min-h-[48px] px-6 py-4 text-lg',
  };

  const handleTouchStart = useCallback(() => {
    if (!disabled) {
      setIsPressed(true);
      // Haptic feedback if available
      if ('vibrate' in navigator) {
        navigator.vibrate(10);
      }
    }
  }, [disabled]);

  const handleTouchEnd = useCallback(() => {
    setIsPressed(false);
  }, []);

  return (
    <button
      className={`
        ${sizeClasses[size]}
        ${className}
        ${isPressed ? 'scale-95 opacity-80' : ''}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        transition-all duration-150 ease-out
        touch-manipulation
        select-none
        rounded-md
        font-medium
        focus:outline-none
        focus:ring-2
        focus:ring-offset-2
        active:scale-95
      `}
      onClick={onClick}
      disabled={disabled}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onMouseLeave={handleTouchEnd}
    >
      {children}
    </button>
  );
};

// Swipe gesture hook
interface SwipeHandlers {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
}

export const useSwipeGestures = (handlers: SwipeHandlers, threshold: number = 50) => {
  const [touchStart, setTouchStart] = useState<{ x: number; y: number } | null>(null);
  const [touchEnd, setTouchEnd] = useState<{ x: number; y: number } | null>(null);

  const onTouchStart = useCallback((e: React.TouchEvent) => {
    setTouchEnd(null);
    setTouchStart({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY,
    });
  }, []);

  const onTouchMove = useCallback((e: React.TouchEvent) => {
    setTouchEnd({
      x: e.targetTouches[0].clientX,
      y: e.targetTouches[0].clientY,
    });
  }, []);

  const onTouchEnd = useCallback(() => {
    if (!touchStart || !touchEnd) return;
    
    const distanceX = touchStart.x - touchEnd.x;
    const distanceY = touchStart.y - touchEnd.y;
    const isLeftSwipe = distanceX > threshold;
    const isRightSwipe = distanceX < -threshold;
    const isUpSwipe = distanceY > threshold;
    const isDownSwipe = distanceY < -threshold;

    if (isLeftSwipe && handlers.onSwipeLeft) {
      handlers.onSwipeLeft();
    }
    if (isRightSwipe && handlers.onSwipeRight) {
      handlers.onSwipeRight();
    }
    if (isUpSwipe && handlers.onSwipeUp) {
      handlers.onSwipeUp();
    }
    if (isDownSwipe && handlers.onSwipeDown) {
      handlers.onSwipeDown();
    }
  }, [touchStart, touchEnd, threshold, handlers]);

  return {
    onTouchStart,
    onTouchMove,
    onTouchEnd,
  };
};

// Mobile-optimized virtual list component
interface VirtualListProps<T> {
  items: T[];
  itemHeight: number;
  containerHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  overscan?: number;
}

export function VirtualList<T>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  overscan = 5,
}: VirtualListProps<T>) {
  const [scrollTop, setScrollTop] = useState(0);
  
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    items.length - 1,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  );
  
  const visibleItems = items.slice(startIndex, endIndex + 1);
  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  return (
    <div
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={handleScroll}
      className="scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100"
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div
          style={{
            transform: `translateY(${offsetY}px)`,
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
          }}
        >
          {visibleItems.map((item, index) =>
            renderItem(item, startIndex + index)
          )}
        </div>
      </div>
    </div>
  );
}

// Intersection observer hook for lazy loading
export const useIntersectionObserver = (
  callback: (entries: IntersectionObserverEntry[]) => void,
  options?: IntersectionObserverInit
) => {
  const [element, setElement] = useState<Element | null>(null);

  useEffect(() => {
    if (!element) return;

    const observer = new IntersectionObserver(callback, {
      threshold: 0.1,
      rootMargin: '50px',
      ...options,
    });

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [element, callback, options]);

  return setElement;
};

// Mobile-specific CSS optimizations
export const mobileStyles = `
  .mobile-device {
    /* Disable hover effects on mobile */
    pointer-events: auto;
  }
  
  .mobile-device *:hover {
    /* Reset hover styles */
  }
  
  .reduce-motion * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  
  /* Touch-friendly scrollbars */
  .scrollbar-thin {
    scrollbar-width: thin;
  }
  
  .scrollbar-thumb-gray-300::-webkit-scrollbar-thumb {
    background-color: #d1d5db;
    border-radius: 4px;
  }
  
  .scrollbar-track-gray-100::-webkit-scrollbar-track {
    background-color: #f3f4f6;
  }
  
  /* Optimize for mobile performance */
  @media (max-width: 768px) {
    * {
      -webkit-tap-highlight-color: transparent;
      -webkit-touch-callout: none;
      -webkit-user-select: none;
      user-select: none;
    }
    
    input, textarea, [contenteditable] {
      -webkit-user-select: text;
      user-select: text;
    }
    
    /* Improve scroll performance */
    .scroll-container {
      -webkit-overflow-scrolling: touch;
      transform: translateZ(0);
    }
  }
`;