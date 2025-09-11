import { forwardRef, useState } from 'react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { slideIn } from '@/utils/animations';

interface ErrorBannerProps {
  message: string;
  onClose?: () => void;
  className?: string;
  dismissible?: boolean;
}

const ErrorBanner = forwardRef<HTMLDivElement, ErrorBannerProps>(
  ({ message, onClose, className, dismissible = true }, ref) => {
    const [isVisible, setIsVisible] = useState(true);

    const handleClose = () => {
      setIsVisible(false);
      onClose?.();
    };

    return (
      <AnimatePresence>
        {isVisible && (
          <motion.div
            ref={ref}
            className={clsx(
              'flex items-center justify-between',
              'p-4 rounded-lg',
              'bg-red-50 border border-red-200',
              'text-red-700',
              className
            )}
            variants={slideIn}
            initial="initial"
            animate="animate"
            exit="exit"
          >
            <div className="flex items-center gap-3">
              <svg 
                className="h-5 w-5 text-red-600 flex-shrink-0" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" 
                />
              </svg>
              <p className="text-sm font-medium">{message}</p>
            </div>
            {dismissible && (
              <button
                onClick={handleClose}
                className="ml-4 text-red-600 hover:text-red-800 transition-colors"
                aria-label="关闭错误提示"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    );
  }
);

ErrorBanner.displayName = 'ErrorBanner';

export { ErrorBanner };
export type { ErrorBannerProps };