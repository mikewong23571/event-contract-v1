'use client';

import React from 'react';
import { Loader2, TrendingUp, BarChart3, AlertCircle } from 'lucide-react';

// 基础加载动画组件
export function LoadingSpinner({ size = 'default', className = '' }: {
  size?: 'sm' | 'default' | 'lg';
  className?: string;
}) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    default: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  return (
    <Loader2 
      className={`animate-spin ${sizeClasses[size]} ${className}`} 
    />
  );
}

// 页面级加载状态
export function PageLoading({ message = '加载中...' }: { message?: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <LoadingSpinner size="lg" className="mx-auto mb-4 text-blue-600" />
        <p className="text-gray-600 text-lg">{message}</p>
      </div>
    </div>
  );
}

// 卡片加载骨架屏
export function CardSkeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`animate-pulse ${className}`}>
      <div className="bg-white rounded-lg shadow p-6">
        <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
        <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
        <div className="h-3 bg-gray-200 rounded w-2/3 mb-4"></div>
        <div className="h-8 bg-gray-200 rounded w-1/4"></div>
      </div>
    </div>
  );
}

// 表格加载骨架屏
export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="animate-pulse">
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {/* 表头 */}
        <div className="bg-gray-50 px-6 py-3 border-b">
          <div className="flex space-x-4">
            {Array.from({ length: cols }).map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded flex-1"></div>
            ))}
          </div>
        </div>
        {/* 表格行 */}
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="px-6 py-4 border-b border-gray-100">
            <div className="flex space-x-4">
              {Array.from({ length: cols }).map((_, colIndex) => (
                <div key={colIndex} className="h-3 bg-gray-200 rounded flex-1"></div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// 图表加载状态
export function ChartSkeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`animate-pulse ${className}`}>
      <div className="bg-white rounded-lg shadow p-6">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-6"></div>
        <div className="h-64 bg-gray-100 rounded flex items-end justify-between px-4 pb-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <div 
              key={i} 
              className="bg-gray-200 rounded-t" 
              style={{ 
                height: `${Math.random() * 80 + 20}%`, 
                width: '6%' 
              }}
            ></div>
          ))}
        </div>
      </div>
    </div>
  );
}

// 信号列表加载状态
export function SignalListSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="animate-pulse">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                <div className="h-4 bg-gray-200 rounded w-24"></div>
              </div>
              <div className="h-6 bg-gray-200 rounded w-16"></div>
            </div>
            <div className="grid grid-cols-3 gap-4 mb-3">
              <div className="h-3 bg-gray-200 rounded"></div>
              <div className="h-3 bg-gray-200 rounded"></div>
              <div className="h-3 bg-gray-200 rounded"></div>
            </div>
            <div className="h-3 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
      ))}
    </div>
  );
}

// 带图标的加载状态
export function IconLoadingState({ 
  icon: Icon = TrendingUp, 
  message = '加载中...', 
  description,
  className = '' 
}: {
  icon?: React.ComponentType<any>;
  message?: string;
  description?: string;
  className?: string;
}) {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center ${className}`}>
      <div className="relative mb-4">
        <Icon className="w-12 h-12 text-gray-400" />
        <LoadingSpinner className="absolute -top-1 -right-1 text-blue-600" size="sm" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{message}</h3>
      {description && (
        <p className="text-gray-600 max-w-sm">{description}</p>
      )}
    </div>
  );
}

// 数据获取加载状态
export function DataFetchingLoader({ type = 'market' }: { type?: 'market' | 'signals' | 'analysis' }) {
  const configs = {
    market: {
      icon: BarChart3,
      message: '获取市场数据',
      description: '正在从数据源获取最新的市场信息...'
    },
    signals: {
      icon: TrendingUp,
      message: '加载交易信号',
      description: '正在分析市场趋势并生成交易信号...'
    },
    analysis: {
      icon: AlertCircle,
      message: '执行分析',
      description: '正在处理数据并生成分析报告...'
    }
  };

  const config = configs[type];

  return (
    <IconLoadingState
      icon={config.icon}
      message={config.message}
      description={config.description}
      className="min-h-[200px]"
    />
  );
}

// 按钮加载状态
export function LoadingButton({ 
  children, 
  loading = false, 
  disabled = false,
  className = '',
  onClick,
  ...props 
}: {
  children: React.ReactNode;
  loading?: boolean;
  disabled?: boolean;
  className?: string;
  onClick?: () => void;
  [key: string]: any;
}) {
  return (
    <button
      className={`
        relative inline-flex items-center justify-center px-4 py-2 
        border border-transparent text-sm font-medium rounded-md 
        text-white bg-blue-600 hover:bg-blue-700 
        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
        disabled:opacity-50 disabled:cursor-not-allowed
        transition-colors duration-200
        ${className}
      `}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading && (
        <LoadingSpinner size="sm" className="mr-2" />
      )}
      {children}
    </button>
  );
}

// 内联加载状态
export function InlineLoader({ message = '加载中...', className = '' }: {
  message?: string;
  className?: string;
}) {
  return (
    <div className={`flex items-center space-x-2 text-gray-600 ${className}`}>
      <LoadingSpinner size="sm" />
      <span className="text-sm">{message}</span>
    </div>
  );
}

// 进度条加载
export function ProgressLoader({ 
  progress = 0, 
  message = '处理中...', 
  className = '' 
}: {
  progress?: number;
  message?: string;
  className?: string;
}) {
  return (
    <div className={`w-full ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">{message}</span>
        <span className="text-sm text-gray-500">{Math.round(progress)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
        ></div>
      </div>
    </div>
  );
}

// 空状态组件
export function EmptyState({ 
  icon: Icon = AlertCircle,
  title = '暂无数据',
  description = '当前没有可显示的内容',
  action,
  className = ''
}: {
  icon?: React.ComponentType<any>;
  title?: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center ${className}`}>
      <Icon className="w-12 h-12 text-gray-400 mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 max-w-sm mb-4">{description}</p>
      {action}
    </div>
  );
}