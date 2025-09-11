import { ButtonHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';
import { buttonHover, buttonTap, loadingSpinner } from '@/utils/animations';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    variant = 'primary', 
    size = 'md', 
    loading = false,
    leftIcon,
    rightIcon,
    children, 
    className, 
    disabled,
    ...props 
  }, ref) => {
    const baseClasses = 'btn transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]';
    
    const variantClasses = {
      primary: 'btn-primary',
      secondary: 'btn-secondary', 
      ghost: 'btn-ghost',
      outline: 'btn-outline',
      danger: 'bg-danger-500 text-white hover:bg-danger-600',
    };

    const sizeClasses = {
      sm: 'h-8 px-3 text-xs',
      md: 'h-10 px-4 text-sm',
      lg: 'h-12 px-6 text-base',
    };

    const { 
      onDrag, 
      onDragStart, 
      onDragEnd, 
      onAnimationStart,
      onAnimationEnd,
      onTransitionEnd,
      ...restProps 
    } = props;

    return (
      <motion.button
        ref={ref}
        className={clsx(
          baseClasses,
          variantClasses[variant],
          sizeClasses[size],
          {
            'opacity-50 cursor-not-allowed': disabled || loading,
          },
          className
        )}
        disabled={disabled || loading}
        whileHover={!disabled && !loading ? buttonHover : undefined}
        whileTap={!disabled && !loading ? buttonTap : undefined}
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
        {...restProps}
      >
        {loading && (
          <motion.div 
            className="w-4 h-4 mr-2 border-2 border-current border-t-transparent rounded-full"
            variants={loadingSpinner}
            animate="animate"
          />
        )}
        {leftIcon && !loading && (
          <motion.span 
            className="mr-2"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            {leftIcon}
          </motion.span>
        )}
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.05 }}
        >
          {children}
        </motion.span>
        {rightIcon && (
          <motion.span 
            className="ml-2"
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            {rightIcon}
          </motion.span>
        )}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';

export { Button };
export type { ButtonProps };