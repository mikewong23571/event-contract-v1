import { HTMLAttributes } from 'react';
import { clsx } from 'clsx';

interface LoadingProps extends HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'spinner' | 'dots' | 'pulse';
  text?: string;
}

const Loading = ({ 
  size = 'md', 
  variant = 'spinner', 
  text,
  className,
  ...props 
}: LoadingProps) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  const renderSpinner = () => (
    <div className={clsx('loading-spinner', sizeClasses[size])} />
  );

  const renderDots = () => (
    <div className="flex space-x-1">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={clsx(
            'bg-primary-500 rounded-full animate-pulse',
            {
              'w-1 h-1': size === 'sm',
              'w-1.5 h-1.5': size === 'md',
              'w-2 h-2': size === 'lg',
            }
          )}
          style={{
            animationDelay: `${i * 0.2}s`,
            animationDuration: '1s',
          }}
        />
      ))}
    </div>
  );

  const renderPulse = () => (
    <div className={clsx(
      'bg-primary-500/20 rounded animate-pulse',
      sizeClasses[size]
    )} />
  );

  const renderVariant = () => {
    switch (variant) {
      case 'dots':
        return renderDots();
      case 'pulse':
        return renderPulse();
      default:
        return renderSpinner();
    }
  };

  return (
    <div 
      className={clsx(
        'flex items-center justify-center',
        {
          'flex-col space-y-2': text,
          'space-x-2': text && variant !== 'dots',
        },
        className
      )}
      {...props}
    >
      {renderVariant()}
      {text && (
        <span className="text-sm text-muted-foreground animate-pulse">
          {text}
        </span>
      )}
    </div>
  );
};

export { Loading };
export type { LoadingProps };