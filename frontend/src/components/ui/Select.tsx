import { SelectHTMLAttributes, forwardRef, useState, useId } from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';
import { fadeIn } from '@/utils/animations';

interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  options: SelectOption[];
  variant?: 'default' | 'error' | 'success';
  selectSize?: 'sm' | 'md' | 'lg';
  error?: string;
  label?: string;
  helperText?: string;
  placeholder?: string;
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ 
    options,
    variant = 'default',
    selectSize = 'md',
    error,
    label,
    helperText,
    placeholder,
    className,
    id,
    onFocus,
    onBlur,
    ...restProps 
  }, ref) => {
    const [isFocused, setIsFocused] = useState(false);
    const reactId = useId();
    const selectId = id || reactId;
    const actualVariant = error ? 'error' : variant;
    
    const baseClasses = 'input appearance-none bg-white cursor-pointer';
    
    const variantClasses = {
      default: 'transition-all duration-200 focus:ring-2 focus:ring-primary-500/20',
      error: 'border-danger-500 focus:border-danger-500 focus:ring-2 focus:ring-danger-500/20',
      success: 'border-success-500 focus:border-success-500 focus:ring-2 focus:ring-success-500/20',
    };

    const handleFocus = (e: React.FocusEvent<HTMLSelectElement>) => {
      setIsFocused(true);
      onFocus?.(e);
    };

    const handleBlur = (e: React.FocusEvent<HTMLSelectElement>) => {
      setIsFocused(false);
      onBlur?.(e);
    };

    const sizeClasses = {
      sm: 'h-8 px-3 text-xs pr-8',
      md: 'h-10 px-3 text-sm pr-10',
      lg: 'h-12 px-4 text-base pr-12',
    };

    return (
      <motion.div 
        className="w-full"
        variants={fadeIn}
        initial="initial"
        animate="animate"
      >
        {label && (
          <motion.label 
            htmlFor={selectId}
            className={clsx(
              'block text-sm font-medium mb-1.5 transition-colors duration-200',
              isFocused ? 'text-primary-500' : 'text-foreground'
            )}
            animate={{
              y: isFocused ? -2 : 0,
              scale: isFocused ? 1.02 : 1
            }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          >
            {label}
          </motion.label>
        )}
        
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={clsx(
              baseClasses,
              variantClasses[actualVariant],
              sizeClasses[selectSize],
              className
            )}
            onFocus={handleFocus}
            onBlur={handleBlur}
            {...restProps}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option 
                key={option.value} 
                value={option.value}
                disabled={option.disabled}
              >
                {option.label}
              </option>
            ))}
          </select>
          
          {/* Custom dropdown arrow */}
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
            <svg 
              className="w-4 h-4 text-gray-400" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M19 9l-7 7-7-7" 
              />
            </svg>
          </div>
        </div>
        
        {(error || helperText) && (
          <motion.p 
            className={clsx(
              'mt-1.5 text-xs',
              error ? 'text-danger-600' : 'text-muted-foreground'
            )}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            {error || helperText}
          </motion.p>
        )}
      </motion.div>
    );
  }
);

Select.displayName = 'Select';

export { Select };
export type { SelectProps, SelectOption };