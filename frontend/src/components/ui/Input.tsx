import { InputHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  variant?: 'default' | 'error' | 'success';
  inputSize?: 'sm' | 'md' | 'lg';
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  error?: string;
  label?: string;
  helperText?: string;
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
    className,
    id,
    ...props 
  }, ref) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    const actualVariant = error ? 'error' : variant;
    
    const baseClasses = 'input';
    
    const variantClasses = {
      default: '',
      error: 'border-danger-500 focus:border-danger-500 focus:ring-danger-500/20',
      success: 'border-success-500 focus:border-success-500 focus:ring-success-500/20',
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

    return (
      <div className="w-full">
        {label && (
          <label 
            htmlFor={inputId}
            className="block text-sm font-medium text-foreground mb-1.5"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className={clsx(
              'absolute left-0 top-0 h-full flex items-center justify-center text-muted-foreground',
              {
                'w-8': inputSize === 'sm',
                'w-10': inputSize === 'md',
                'w-12': inputSize === 'lg',
              }
            )}>
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={clsx(
              baseClasses,
              variantClasses[actualVariant],
              sizeClasses[inputSize],
              iconPadding[inputSize],
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className={clsx(
              'absolute right-0 top-0 h-full flex items-center justify-center text-muted-foreground',
              {
                'w-8': inputSize === 'sm',
                'w-10': inputSize === 'md',
                'w-12': inputSize === 'lg',
              }
            )}>
              {rightIcon}
            </div>
          )}
        </div>
        {(error || helperText) && (
          <p className={clsx(
            'mt-1.5 text-xs',
            {
              'text-danger-600': error,
              'text-muted-foreground': !error && helperText,
            }
          )}>
            {error || helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input };
export type { InputProps };