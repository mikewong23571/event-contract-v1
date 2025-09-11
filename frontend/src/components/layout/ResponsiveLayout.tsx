'use client';

import React from 'react';
import { useMediaQuery } from '@/hooks/use-media-query';

interface ResponsiveLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({
  children,
  className = '',
}) => {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const isTablet = useMediaQuery('(min-width: 769px) and (max-width: 1024px)');
  const isDesktop = useMediaQuery('(min-width: 1025px)');

  return (
    <div
      className={`
        ${className}
        ${isMobile ? 'mobile-layout' : ''}
        ${isTablet ? 'tablet-layout' : ''}
        ${isDesktop ? 'desktop-layout' : ''}
        transition-all duration-300 ease-in-out
      `}
    >
      {children}
    </div>
  );
};

// Responsive grid component
interface ResponsiveGridProps {
  children: React.ReactNode;
  cols?: {
    mobile?: number;
    tablet?: number;
    desktop?: number;
  };
  gap?: string;
  className?: string;
}

export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  cols = { mobile: 1, tablet: 2, desktop: 3 },
  gap = '1rem',
  className = '',
}) => {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const isTablet = useMediaQuery('(min-width: 769px) and (max-width: 1024px)');

  const getCurrentCols = () => {
    if (isMobile) return cols.mobile || 1;
    if (isTablet) return cols.tablet || 2;
    return cols.desktop || 3;
  };

  return (
    <div
      className={`grid ${className}`}
      style={{
        gridTemplateColumns: `repeat(${getCurrentCols()}, 1fr)`,
        gap,
      }}
    >
      {children}
    </div>
  );
};

// Responsive container with max widths
interface ResponsiveContainerProps {
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  className?: string;
}

export const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  size = 'lg',
  className = '',
}) => {
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-4xl',
    xl: 'max-w-6xl',
    full: 'max-w-full',
  };

  return (
    <div
      className={`
        ${sizeClasses[size]}
        ${className}
        mx-auto
        px-4
        sm:px-6
        lg:px-8
        w-full
      `}
    >
      {children}
    </div>
  );
};

// Responsive text component
interface ResponsiveTextProps {
  children: React.ReactNode;
  size?: {
    mobile?: string;
    tablet?: string;
    desktop?: string;
  };
  className?: string;
}

export const ResponsiveText: React.FC<ResponsiveTextProps> = ({
  children,
  size = { mobile: 'text-sm', tablet: 'text-base', desktop: 'text-lg' },
  className = '',
}) => {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const isTablet = useMediaQuery('(min-width: 769px) and (max-width: 1024px)');

  const getCurrentSize = () => {
    if (isMobile) return size.mobile || 'text-sm';
    if (isTablet) return size.tablet || 'text-base';
    return size.desktop || 'text-lg';
  };

  return (
    <span className={`${getCurrentSize()} ${className}`}>
      {children}
    </span>
  );
};

// Mobile-first navigation component
interface MobileNavigationProps {
  items: Array<{
    label: string;
    href: string;
    icon?: React.ReactNode;
  }>;
  onItemClick?: (href: string) => void;
}

export const MobileNavigation: React.FC<MobileNavigationProps> = ({
  items,
  onItemClick,
}) => {
  const isMobile = useMediaQuery('(max-width: 768px)');

  if (!isMobile) {
    // Desktop horizontal navigation
    return (
      <nav className="flex space-x-6">
        {items.map((item, index) => (
          <button
            key={index}
            onClick={() => onItemClick?.(item.href)}
            className="
              flex items-center space-x-2
              px-3 py-2
              text-sm font-medium
              text-gray-700 hover:text-gray-900
              transition-colors duration-200
            "
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
    );
  }

  // Mobile bottom navigation
  return (
    <nav className="
      fixed bottom-0 left-0 right-0
      bg-white border-t border-gray-200
      px-4 py-2
      z-50
    ">
      <div className="flex justify-around">
        {items.map((item, index) => (
          <button
            key={index}
            onClick={() => onItemClick?.(item.href)}
            className="
              flex flex-col items-center
              min-w-[60px] py-2
              text-xs font-medium
              text-gray-600 hover:text-gray-900
              transition-colors duration-200
            "
          >
            {item.icon && (
              <div className="mb-1">
                {item.icon}
              </div>
            )}
            <span className="truncate">{item.label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
};

// Responsive modal component
interface ResponsiveModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
}

export const ResponsiveModal: React.FC<ResponsiveModalProps> = ({
  isOpen,
  onClose,
  children,
  title,
}) => {
  const isMobile = useMediaQuery('(max-width: 768px)');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className={`
            relative w-full bg-white rounded-lg shadow-xl
            ${isMobile 
              ? 'max-w-sm mx-4 max-h-[90vh]' 
              : 'max-w-lg max-h-[80vh]'
            }
            overflow-hidden
          `}
        >
          {/* Header */}
          {title && (
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold">{title}</h3>
              <button
                onClick={onClose}
                className="
                  p-2 hover:bg-gray-100 rounded-full
                  transition-colors duration-200
                "
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}
          
          {/* Content */}
          <div className="p-4 overflow-y-auto max-h-[calc(90vh-8rem)]">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

// Responsive image component with lazy loading
interface ResponsiveImageProps {
  src: string;
  alt: string;
  sizes?: {
    mobile?: string;
    tablet?: string;
    desktop?: string;
  };
  className?: string;
  loading?: 'lazy' | 'eager';
}

export const ResponsiveImage: React.FC<ResponsiveImageProps> = ({
  src,
  alt,
  sizes,
  className = '',
  loading = 'lazy',
}) => {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const isTablet = useMediaQuery('(min-width: 769px) and (max-width: 1024px)');

  const getCurrentSrc = () => {
    if (sizes) {
      if (isMobile && sizes.mobile) return sizes.mobile;
      if (isTablet && sizes.tablet) return sizes.tablet;
      if (sizes.desktop) return sizes.desktop;
    }
    return src;
  };

  return (
    <img
      src={getCurrentSrc()}
      alt={alt}
      loading={loading}
      className={`
        ${className}
        max-w-full h-auto
        transition-opacity duration-300
      `}
      onLoad={(e) => {
        e.currentTarget.style.opacity = '1';
      }}
      style={{ opacity: 0 }}
    />
  );
};