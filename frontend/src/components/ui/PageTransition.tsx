import { motion, AnimatePresence } from 'framer-motion';
import { ReactNode } from 'react';

interface PageTransitionProps {
  children: ReactNode;
  className?: string;
  variant?: 'fade' | 'slide' | 'scale' | 'slideUp';
}

const pageVariants = {
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },
  slide: {
    initial: { x: 300, opacity: 0 },
    animate: { x: 0, opacity: 1 },
    exit: { x: -300, opacity: 0 },
  },
  slideUp: {
    initial: { y: 50, opacity: 0 },
    animate: { y: 0, opacity: 1 },
    exit: { y: -50, opacity: 0 },
  },
  scale: {
    initial: { scale: 0.8, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    exit: { scale: 1.1, opacity: 0 },
  },
};

const pageTransitions = {
  fade: {
    type: 'tween' as const,
    duration: 0.3,
    ease: 'easeInOut' as const,
  },
  slide: {
    type: 'spring' as const,
    stiffness: 300,
    damping: 30,
  },
  slideUp: {
    type: 'spring' as const,
    stiffness: 400,
    damping: 25,
  },
  scale: {
    type: 'spring' as const,
    stiffness: 300,
    damping: 30,
  },
};

export const PageTransition = ({ 
  children, 
  className = '', 
  variant = 'fade' 
}: PageTransitionProps) => {
  return (
    <motion.div
      className={className}
      variants={pageVariants[variant]}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={pageTransitions[variant]}
    >
      {children}
    </motion.div>
  );
};

export const PageWrapper = ({ 
  children, 
  className = '',
  variant = 'slideUp'
}: PageTransitionProps) => {
  return (
    <AnimatePresence mode="wait">
      <PageTransition className={className} variant={variant}>
        {children}
      </PageTransition>
    </AnimatePresence>
  );
};

// 页面容器组件，用于统一页面布局和动效
export const PageContainer = ({ 
  children, 
  className = '',
  title,
  subtitle,
  showHeader = true
}: {
  children: ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  showHeader?: boolean;
}) => {
  return (
    <PageWrapper className={`min-h-screen ${className}`}>
      <div className="container mx-auto px-4 py-6">
        {showHeader && (title || subtitle) && (
          <motion.div 
            className="mb-8"
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1, duration: 0.5 }}
          >
            {title && (
              <motion.h1 
                className="text-3xl font-bold text-foreground mb-2"
                initial={{ y: -10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2, duration: 0.5 }}
              >
                {title}
              </motion.h1>
            )}
            {subtitle && (
              <motion.p 
                className="text-muted-foreground text-lg"
                initial={{ y: -10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3, duration: 0.5 }}
              >
                {subtitle}
              </motion.p>
            )}
          </motion.div>
        )}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.5 }}
        >
          {children}
        </motion.div>
      </div>
    </PageWrapper>
  );
};

export default PageTransition;