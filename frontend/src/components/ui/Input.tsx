import { InputHTMLAttributes, forwardRef, useState } from 'react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { fadeIn, slideIn, scaleIn } from '@/utils/animations';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  variant?: 'default' | 'error' | 'success';
  inputSize?: 'sm' | 'md' | 'lg';
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  error?: string;
  label?: string;
  helperText?: string;
  animated?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ 
    variant = 'default',
    inputSize = 'md',
    leftIcon,
    rightIcon,
    error,
    label,
    helperText,
    animated = true,
    className,
    id,
    onFocus,
    onBlur,
    onDrag,
    onDragStart,
    onDragEnd,
    onAnimationStart,
    onAnimationEnd,
    onTransitionEnd,
    ...restProps 
  }, ref) => {
    const [isFocused, setIsFocused] = useState(false);
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    const actualVariant = error ? 'error' : variant;
    
    const baseClasses = 'input';
    
    const variantClasses = {
      default: 'transition-all duration-200 focus:ring-2 focus:ring-primary-500/20',
      error: 'border-danger-500 focus:border-danger-500 focus:ring-2 focus:ring-danger-500/20',
      success: 'border-success-500 focus:border-success-500 focus:ring-2 focus:ring-success-500/20',
    };

    const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
      setIsFocused(true);
      onFocus?.(e);
    };

    const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
      setIsFocused(false);
      onBlur?.(e);
    };

    const sizeClasses = {
      sm: 'h-8 px-3 text-xs',
      md: 'h-10 px-3 text-sm',
      lg: 'h-12 px-4 text-base',
    };

    const iconPadding = {
      sm: leftIcon ? 'pl-8' : rightIcon ? 'pr-8' : '',
      md: leftIcon ? 'pl-10' : rightIcon ? 'pr-10' : '',
      lg: leftIcon ? 'pl-12' : rightIcon ? 'pr-12' : '',
    };

    const InputComponent = animated ? motion.input : 'input';
    const motionProps = animated ? {
      whileFocus: { scale: 1.02 },
      transition: { type: 'spring', stiffness: 300, damping: 30 }
    } : {};

    return (
      <motion.div 
        className="w-full"
        variants={animated ? fadeIn : undefined}
        initial={animated ? 'initial' : undefined}
        animate={animated ? 'animate' : undefined}
      >
        {label && (
          <motion.label 
            htmlFor={inputId}
            className={clsx(
              'block text-sm font-medium mb-1.5 transition-colors duration-200',
              isFocused ? 'text-primary-500' : 'text-foreground'
            )}
            animate={animated ? {
              y: isFocused ? -2 : 0,
              scale: isFocused ? 1.02 : 1
            } : undefined}
            transition={animated ? { type: 'spring', stiffness: 300, damping: 30 } : undefined}
          >
            {label}
          </motion.label>
        )}
        <div className="relative">
          {leftIcon && (
            <motion.div 
              className={clsx(
                'absolute left-0 top-0 h-full flex items-center justify-center transition-colors duration-200',
                isFocused ? 'text-primary-500' : 'text-muted-foreground',
                {
                  'w-8': inputSize === 'sm',
                  'w-10': inputSize === 'md',
                  'w-12': inputSize === 'lg',
                }
              )}
              animate={animated ? {
                scale: isFocused ? 1.1 : 1,
                x: isFocused ? 2 : 0
              } : undefined}
              transition={animated ? { type: 'spring', stiffness: 300, damping: 30 } : undefined}
            >
              {leftIcon}
            </motion.div>
          )}
          <InputComponent
            ref={ref}
            id={inputId}
            className={clsx(
              baseClasses,
              variantClasses[actualVariant],
              sizeClasses[inputSize],
              iconPadding[inputSize],
              className
            )}
            onFocus={handleFocus}
            onBlur={handleBlur}
            {...(animated ? motionProps : {})}
            {...restProps}
          />
          {rightIcon && (
            <motion.div 
              className={clsx(
                'absolute right-0 top-0 h-full flex items-center justify-center transition-colors duration-200',
                isFocused ? 'text-primary-500' : 'text-muted-foreground',
                {
                  'w-8': inputSize === 'sm',
                  'w-10': inputSize === 'md',
                  'w-12': inputSize === 'lg',
                }
              )}
              animate={animated ? {
                scale: isFocused ? 1.1 : 1,
                x: isFocused ? -2 : 0
              } : undefined}
              transition={animated ? { type: 'spring', stiffness: 300, damping: 30 } : undefined}
            >
              {rightIcon}
            </motion.div>
          )}
        </div>
        <AnimatePresence mode="wait">
          {(error || helperText) && (
            <motion.p 
              className={clsx(
                'mt-1.5 text-xs',
                {
                  'text-danger-600': error,
                  'text-muted-foreground': !error && helperText,
                }
              )}
              variants={animated ? slideIn : undefined}
              initial={animated ? 'initial' : undefined}
              animate={animated ? 'animate' : undefined}
              exit={animated ? 'exit' : undefined}
              key={error ? 'error' : 'helper'}
            >
              {error || helperText}
            </motion.p>
          )}
        </AnimatePresence>
      </motion.div>
    );
  }
);

Input.displayName = 'Input';

export { Input };
export type { InputProps };