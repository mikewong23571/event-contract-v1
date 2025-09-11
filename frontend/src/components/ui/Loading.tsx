import { HTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';
import { loadingSpinner, loadingPulse, fadeIn } from '@/utils/animations';

interface LoadingProps extends HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'spinner' | 'dots' | 'pulse' | 'bars';
  text?: string;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
}

const Loading = ({ 
  size = 'md', 
  variant = 'spinner', 
  text,
  color = 'primary',
  className,
  onDrag,
  onDragStart,
  onDragEnd,
  onAnimationStart,
  onAnimationEnd,
  onTransitionEnd,
  ...restProps 
}: LoadingProps) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  const colorClasses = {
    primary: 'text-primary-500 border-primary-500',
    secondary: 'text-secondary-500 border-secondary-500',
    success: 'text-success-500 border-success-500',
    warning: 'text-warning-500 border-warning-500',
    danger: 'text-danger-500 border-danger-500',
  };

  const renderSpinner = () => (
    <motion.div 
      className={clsx(
        'border-2 border-t-transparent rounded-full',
        sizeClasses[size],
        colorClasses[color]
      )}
      variants={loadingSpinner}
      animate="animate"
    />
  );

  const renderDots = () => (
    <div className="flex space-x-1">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className={clsx(
            'rounded-full',
            {
              'w-1 h-1': size === 'sm',
              'w-1.5 h-1.5': size === 'md',
              'w-2 h-2': size === 'lg',
            },
            `bg-${color}-500`
          )}
          animate={{
            scale: [1, 1.2, 1],
            opacity: [0.7, 1, 0.7],
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
            delay: i * 0.2,
            ease: 'easeInOut'
          }}
        />
      ))}
    </div>
  );

  const renderPulse = () => (
    <motion.div 
      className={clsx(
        'rounded',
        sizeClasses[size],
        `bg-${color}-500/20`
      )}
      variants={loadingPulse}
      animate="animate"
    />
  );

  const renderBars = () => (
    <div className="flex space-x-1 items-end">
      {[0, 1, 2, 3].map((i) => (
        <motion.div
          key={i}
          className={clsx(
            'rounded-sm',
            {
              'w-1': size === 'sm',
              'w-1.5': size === 'md', 
              'w-2': size === 'lg',
            },
            `bg-${color}-500`
          )}
          animate={{
            height: [
              size === 'sm' ? '4px' : size === 'md' ? '6px' : '8px',
              size === 'sm' ? '16px' : size === 'md' ? '24px' : '32px',
              size === 'sm' ? '4px' : size === 'md' ? '6px' : '8px'
            ]
          }}
          transition={{
            duration: 0.8,
            repeat: Infinity,
            delay: i * 0.1,
            ease: 'easeInOut'
          }}
        />
      ))}
    </div>
  );

  const renderVariant = () => {
    switch (variant) {
      case 'dots':
        return renderDots();
      case 'pulse':
        return renderPulse();
      case 'bars':
        return renderBars();
      default:
        return renderSpinner();
    }
  };

  return (
    <motion.div 
      className={clsx(
        'flex items-center justify-center',
        {
          'flex-col space-y-2': text,
          'space-x-2': text && variant !== 'dots' && variant !== 'bars',
        },
        className
      )}
      variants={fadeIn}
       initial="initial"
       animate="animate"
       {...restProps}
    >
      {renderVariant()}
      {text && (
        <motion.span 
          className="text-sm text-muted-foreground"
          animate={{
            opacity: [0.5, 1, 0.5]
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeInOut'
          }}
        >
          {text}
        </motion.span>
      )}
    </motion.div>
  );
};

export { Loading };
export type { LoadingProps };