'use client';

import React, { useState, useEffect } from 'react';
import { Check, X, AlertTriangle, Info, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

// 通知类型
type NotificationType = 'success' | 'error' | 'warning' | 'info';

// 通知项接口
interface NotificationItem {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number;
  persistent?: boolean;
}

// 通知管理器
class NotificationManager {
  private static instance: NotificationManager;
  private notifications: NotificationItem[] = [];
  private listeners: ((notifications: NotificationItem[]) => void)[] = [];

  static getInstance(): NotificationManager {
    if (!NotificationManager.instance) {
      NotificationManager.instance = new NotificationManager();
    }
    return NotificationManager.instance;
  }

  subscribe(listener: (notifications: NotificationItem[]) => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notify() {
    this.listeners.forEach(listener => listener([...this.notifications]));
  }

  add(notification: Omit<NotificationItem, 'id'>) {
    const id = Math.random().toString(36).substr(2, 9);
    const newNotification: NotificationItem = {
      id,
      duration: 5000,
      ...notification,
    };

    this.notifications.push(newNotification);
    this.notify();

    // 自动移除（除非是持久通知）
    if (!newNotification.persistent && newNotification.duration) {
      setTimeout(() => {
        this.remove(id);
      }, newNotification.duration);
    }

    return id;
  }

  remove(id: string) {
    this.notifications = this.notifications.filter(n => n.id !== id);
    this.notify();
  }

  clear() {
    this.notifications = [];
    this.notify();
  }

  // 便捷方法
  success(title: string, message?: string, options?: Partial<NotificationItem>) {
    return this.add({ type: 'success', title, message, ...options });
  }

  error(title: string, message?: string, options?: Partial<NotificationItem>) {
    return this.add({ type: 'error', title, message, ...options });
  }

  warning(title: string, message?: string, options?: Partial<NotificationItem>) {
    return this.add({ type: 'warning', title, message, ...options });
  }

  info(title: string, message?: string, options?: Partial<NotificationItem>) {
    return this.add({ type: 'info', title, message, ...options });
  }
}

// 导出通知管理器实例
export const notifications = NotificationManager.getInstance();

// 通知组件
export function NotificationContainer() {
  const [notificationList, setNotificationList] = useState<NotificationItem[]>([]);

  useEffect(() => {
    const unsubscribe = notifications.subscribe(setNotificationList);
    return unsubscribe;
  }, []);

  const getIcon = (type: NotificationType) => {
    switch (type) {
      case 'success':
        return CheckCircle;
      case 'error':
        return XCircle;
      case 'warning':
        return AlertTriangle;
      case 'info':
        return Info;
      default:
        return Info;
    }
  };

  const getStyles = (type: NotificationType) => {
    switch (type) {
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-sm">
      {notificationList.map((notification) => {
        const Icon = getIcon(notification.type);
        return (
          <div
            key={notification.id}
            className={`
              p-4 rounded-lg border shadow-lg transform transition-all duration-300
              animate-in slide-in-from-right-full
              ${getStyles(notification.type)}
            `}
          >
            <div className="flex items-start">
              <Icon className="w-5 h-5 mt-0.5 mr-3 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-sm">{notification.title}</h4>
                {notification.message && (
                  <p className="mt-1 text-sm opacity-90">{notification.message}</p>
                )}
              </div>
              <button
                onClick={() => notifications.remove(notification.id)}
                className="ml-3 flex-shrink-0 opacity-70 hover:opacity-100 transition-opacity"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// 确认对话框
export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title = '确认操作',
  message = '您确定要执行此操作吗？',
  confirmText = '确认',
  cancelText = '取消',
  type = 'warning'
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  message?: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'warning' | 'danger' | 'info';
}) {
  if (!open) return null;

  const getButtonStyles = () => {
    switch (type) {
      case 'danger':
        return 'bg-red-600 hover:bg-red-700 text-white';
      case 'warning':
        return 'bg-yellow-600 hover:bg-yellow-700 text-white';
      case 'info':
        return 'bg-blue-600 hover:bg-blue-700 text-white';
      default:
        return 'bg-gray-600 hover:bg-gray-700 text-white';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 背景遮罩 */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />
      
      {/* 对话框 */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 transform transition-all">
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">{title}</h3>
          <p className="text-gray-600 mb-6">{message}</p>
          
          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            >
              {cancelText}
            </button>
            <button
              onClick={() => {
                onConfirm();
                onClose();
              }}
              className={`px-4 py-2 rounded-md transition-colors ${getButtonStyles()}`}
            >
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// 工具提示
export function Tooltip({
  children,
  content,
  position = 'top',
  className = ''
}: {
  children: React.ReactNode;
  content: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
}) {
  const [visible, setVisible] = useState(false);

  const getPositionStyles = () => {
    switch (position) {
      case 'top':
        return 'bottom-full left-1/2 transform -translate-x-1/2 mb-2';
      case 'bottom':
        return 'top-full left-1/2 transform -translate-x-1/2 mt-2';
      case 'left':
        return 'right-full top-1/2 transform -translate-y-1/2 mr-2';
      case 'right':
        return 'left-full top-1/2 transform -translate-y-1/2 ml-2';
      default:
        return 'bottom-full left-1/2 transform -translate-x-1/2 mb-2';
    }
  };

  return (
    <div 
      className={`relative inline-block ${className}`}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div className={`absolute z-10 ${getPositionStyles()}`}>
          <div className="bg-gray-900 text-white text-sm px-2 py-1 rounded whitespace-nowrap">
            {content}
          </div>
        </div>
      )}
    </div>
  );
}

// 状态指示器
export function StatusIndicator({
  status,
  label,
  showLabel = true,
  size = 'default',
  className = ''
}: {
  status: 'online' | 'offline' | 'loading' | 'error' | 'warning';
  label?: string;
  showLabel?: boolean;
  size?: 'sm' | 'default' | 'lg';
  className?: string;
}) {
  const sizeClasses = {
    sm: 'w-2 h-2',
    default: 'w-3 h-3',
    lg: 'w-4 h-4'
  };

  const getStatusStyles = () => {
    switch (status) {
      case 'online':
        return 'bg-green-500';
      case 'offline':
        return 'bg-gray-400';
      case 'loading':
        return 'bg-blue-500 animate-pulse';
      case 'error':
        return 'bg-red-500';
      case 'warning':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getLabel = () => {
    if (label) return label;
    switch (status) {
      case 'online':
        return '在线';
      case 'offline':
        return '离线';
      case 'loading':
        return '连接中';
      case 'error':
        return '错误';
      case 'warning':
        return '警告';
      default:
        return '未知';
    }
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className={`rounded-full ${sizeClasses[size]} ${getStatusStyles()}`} />
      {showLabel && (
        <span className="text-sm text-gray-600">{getLabel()}</span>
      )}
    </div>
  );
}

// 复制到剪贴板
export function CopyToClipboard({
  text,
  children,
  onCopy,
  className = ''
}: {
  text: string;
  children?: React.ReactNode;
  onCopy?: () => void;
  className?: string;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      onCopy?.();
      notifications.success('已复制到剪贴板');
      
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      notifications.error('复制失败', '请手动复制内容');
    }
  };

  return (
    <button
      onClick={handleCopy}
      className={`
        inline-flex items-center space-x-1 text-sm text-gray-600 
        hover:text-gray-800 transition-colors
        ${className}
      `}
    >
      {children || (
        <>
          {copied ? (
            <Check className="w-4 h-4 text-green-600" />
          ) : (
            <span>复制</span>
          )}
        </>
      )}
    </button>
  );
}

// 键盘快捷键提示
export function KeyboardShortcut({
  keys,
  description,
  className = ''
}: {
  keys: string[];
  description?: string;
  className?: string;
}) {
  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className="flex items-center space-x-1">
        {keys.map((key, index) => (
          <React.Fragment key={key}>
            {index > 0 && <span className="text-gray-400">+</span>}
            <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-200 rounded">
              {key}
            </kbd>
          </React.Fragment>
        ))}
      </div>
      {description && (
        <span className="text-sm text-gray-600">{description}</span>
      )}
    </div>
  );
}

// 使用通知的Hook
export function useNotifications() {
  return {
    success: notifications.success.bind(notifications),
    error: notifications.error.bind(notifications),
    warning: notifications.warning.bind(notifications),
    info: notifications.info.bind(notifications),
    clear: notifications.clear.bind(notifications)
  };
}

// 确认对话框Hook
export function useConfirm() {
  const [dialog, setDialog] = useState<{
    open: boolean;
    title?: string;
    message?: string;
    onConfirm?: () => void;
    type?: 'warning' | 'danger' | 'info';
  }>({ open: false });

  const confirm = (options: {
    title?: string;
    message?: string;
    type?: 'warning' | 'danger' | 'info';
  } = {}) => {
    return new Promise<boolean>((resolve) => {
      setDialog({
        open: true,
        ...options,
        onConfirm: () => resolve(true)
      });
    });
  };

  const ConfirmDialogComponent = () => (
    <ConfirmDialog
      {...dialog}
      onClose={() => {
        setDialog({ open: false });
      }}
      onConfirm={() => {
        dialog.onConfirm?.();
        setDialog({ open: false });
      }}
    />
  );

  return { confirm, ConfirmDialog: ConfirmDialogComponent };
}