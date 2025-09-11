import { forwardRef, useState, useEffect } from 'react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { slideIn } from '@/utils/animations';

interface SuccessNoteProps {
  message: string;
  durationMs?: number;
  onClose?: () => void;
  className?: string;
  dismissible?: boolean;
}

const SuccessNote = forwardRef<HTMLDivElement, SuccessNoteProps>(
  ({ message, durationMs = 3000, onClose, className, dismissible = true }, ref) => {
    const [isVisible, setIsVisible] = useState(true);

    const handleClose = () => {
      setIsVisible(false);
      onClose?.();
    };

    useEffect(() => {
      if (durationMs > 0) {
        const timer = setTimeout(() => {
          handleClose();
        }, durationMs);
        return () => clearTimeout(timer);
      }
    }, [durationMs]);

    return (
      <AnimatePresence>
        {isVisible && (
          <motion.div
            ref={ref}
            className={clsx(
              'flex items-center justify-between',
              'p-4 rounded-lg',
              'bg-green-50 border border-green-200',
              'text-green-700',
              className
            )}
            variants={slideIn}
            initial="initial"
            animate="animate"
            exit="exit"
          >
            <div className="flex items-center gap-3">
              <svg 
                className="h-5 w-5 text-green-600 flex-shrink-0" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" 
                />
              </svg>
              <p className="text-sm font-medium">{message}</p>
            </div>
            {dismissible && (
              <button
                onClick={handleClose}
                className="ml-4 text-green-600 hover:text-green-800 transition-colors"
                aria-label="关闭成功提示"
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

SuccessNote.displayName = 'SuccessNote';

export { SuccessNote };
export type { SuccessNoteProps };