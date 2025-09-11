import { ReactNode, forwardRef } from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';
import { fadeIn } from '@/utils/animations';

interface ControlBarProps {
  children: ReactNode;
  className?: string;
}

const ControlBar = forwardRef<HTMLDivElement, ControlBarProps>(
  ({ children, className }, ref) => {
    return (
      <motion.div
        ref={ref}
        className={clsx(
          // 小屏纵向堆叠，≥sm 水平流动，允许换行
          'flex flex-col gap-y-2 sm:flex-row sm:flex-wrap sm:items-center',
          // 控件间距
          'gap-x-3',
          // 与下方内容的间距
          'mb-4 sm:mb-6',
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

ControlBar.displayName = 'ControlBar';

export { ControlBar };
export type { ControlBarProps };