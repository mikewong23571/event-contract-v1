import { forwardRef } from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';
import { fadeIn } from '@/utils/animations';

type StatusType = 'success' | 'warning' | 'error' | 'idle' | 'loading';

interface StatusIndicatorProps {
  status: StatusType;
  text: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const StatusIndicator = forwardRef<HTMLDivElement, StatusIndicatorProps>(
  ({ status, text, className, size = 'md' }, ref) => {
    const statusConfig = {
      success: {
        dotColor: 'bg-green-500',
        textColor: 'text-green-700',
        bgColor: 'bg-green-50',
      },
      warning: {
        dotColor: 'bg-yellow-500',
        textColor: 'text-yellow-700',
        bgColor: 'bg-yellow-50',
      },
      error: {
        dotColor: 'bg-red-500',
        textColor: 'text-red-700',
        bgColor: 'bg-red-50',
      },
      idle: {
        dotColor: 'bg-gray-400',
        textColor: 'text-gray-600',
        bgColor: 'bg-gray-50',
      },
      loading: {
        dotColor: 'bg-blue-500',
        textColor: 'text-blue-700',
        bgColor: 'bg-blue-50',
      },
    };

    const sizeConfig = {
      sm: {
        dot: 'w-2 h-2',
        text: 'text-xs',
        padding: 'px-2 py-1',
        gap: 'gap-1.5',
      },
      md: {
        dot: 'w-2.5 h-2.5',
        text: 'text-sm',
        padding: 'px-3 py-1.5',
        gap: 'gap-2',
      },
      lg: {
        dot: 'w-3 h-3',
        text: 'text-base',
        padding: 'px-4 py-2',
        gap: 'gap-2.5',
      },
    };

    const config = statusConfig[status];
    const sizeStyles = sizeConfig[size];

    return (
      <motion.div
        ref={ref}
        className={clsx(
          'inline-flex items-center rounded-full',
          config.bgColor,
          sizeStyles.padding,
          sizeStyles.gap,
          className
        )}
        variants={fadeIn}
        initial="initial"
        animate="animate"
      >
        <motion.div
          className={clsx(
            'rounded-full flex-shrink-0',
            config.dotColor,
            sizeStyles.dot
          )}
          animate={status === 'loading' ? {
            scale: [1, 1.2, 1],
            opacity: [1, 0.7, 1],
          } : undefined}
          transition={status === 'loading' ? {
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeInOut',
          } : undefined}
        />
        <span className={clsx(
          'font-medium',
          config.textColor,
          sizeStyles.text
        )}>
          {text}
        </span>
      </motion.div>
    );
  }
);

StatusIndicator.displayName = 'StatusIndicator';

export { StatusIndicator };
export type { StatusIndicatorProps, StatusType };