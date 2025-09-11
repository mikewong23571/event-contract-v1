import { ReactNode, forwardRef } from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';
import { fadeIn } from '@/utils/animations';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  className?: string;
}

const PageHeader = forwardRef<HTMLDivElement, PageHeaderProps>(
  ({ title, subtitle, actions, className }, ref) => {
    return (
      <motion.div
        ref={ref}
        className={clsx(
          'flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between',
          className
        )}
        variants={fadeIn}
        initial="initial"
        animate="animate"
      >
        <div className="flex-1">
          <h2 className="text-xl font-semibold text-gray-900">
            {title}
          </h2>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">
              {subtitle}
            </p>
          )}
        </div>
        {actions && (
          <div className="flex-shrink-0">
            {actions}
          </div>
        )}
      </motion.div>
    );
  }
);

PageHeader.displayName = 'PageHeader';

export { PageHeader };
export type { PageHeaderProps };