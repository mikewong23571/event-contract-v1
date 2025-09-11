import { ReactNode, forwardRef } from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';
import { fadeIn } from '@/utils/animations';

interface FormGridProps {
  children: ReactNode;
  colsSm?: number;
  colsMd?: number;
  colsLg?: number;
  className?: string;
}

const FormGrid = forwardRef<HTMLDivElement, FormGridProps>(
  ({ children, colsSm = 1, colsMd = 2, colsLg = 3, className }, ref) => {
    const getGridCols = (cols: number) => {
      const colsMap: Record<number, string> = {
        1: 'grid-cols-1',
        2: 'grid-cols-2',
        3: 'grid-cols-3',
        4: 'grid-cols-4',
        5: 'grid-cols-5',
        6: 'grid-cols-6',
      };
      return colsMap[cols] || 'grid-cols-1';
    };

    return (
      <motion.div
        ref={ref}
        className={clsx(
          'grid gap-4',
          // 响应式列数
          getGridCols(colsSm),
          `sm:${getGridCols(colsMd)}`,
          `lg:${getGridCols(colsLg)}`,
          className
        )}
        variants={fadeIn}
        initial="initial"
        animate="animate"
      >
        {children}
      </motion.div>
    );
  }
);

FormGrid.displayName = 'FormGrid';

export { FormGrid };
export type { FormGridProps };