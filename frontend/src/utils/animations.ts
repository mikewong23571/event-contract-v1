import { Variants, Transition } from 'framer-motion';

// 基础过渡配置
export const transitions = {
  fast: { duration: 0.15, ease: 'easeOut' } as Transition,
  normal: { duration: 0.25, ease: 'easeOut' } as Transition,
  slow: { duration: 0.35, ease: 'easeOut' } as Transition,
  spring: {
    type: 'spring',
    stiffness: 300,
    damping: 30,
  } as Transition,
  springBouncy: {
    type: 'spring',
    stiffness: 400,
    damping: 25,
  } as Transition,
};

// 淡入动画变体
export const fadeIn: Variants = {
  initial: { 
    opacity: 0, 
    y: 20 
  },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: transitions.normal
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: transitions.fast
  }
};

// 滑入动画变体
export const slideIn: Variants = {
  initial: { 
    opacity: 0, 
    x: -20 
  },
  animate: { 
    opacity: 1, 
    x: 0,
    transition: transitions.normal
  },
  exit: {
    opacity: 0,
    x: 20,
    transition: transitions.fast
  }
};

// 右侧滑入
export const slideInRight: Variants = {
  initial: { 
    opacity: 0, 
    x: 20 
  },
  animate: { 
    opacity: 1, 
    x: 0,
    transition: transitions.normal
  },
  exit: {
    opacity: 0,
    x: -20,
    transition: transitions.fast
  }
};

// 上方滑入
export const slideInUp: Variants = {
  initial: { 
    opacity: 0, 
    y: 20 
  },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: transitions.normal
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: transitions.fast
  }
};

// 下方滑入
export const slideInDown: Variants = {
  initial: { 
    opacity: 0, 
    y: -20 
  },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: transitions.normal
  },
  exit: {
    opacity: 0,
    y: 20,
    transition: transitions.fast
  }
};

// 缩放动画变体
export const scaleIn: Variants = {
  initial: { 
    opacity: 0, 
    scale: 0.95 
  },
  animate: { 
    opacity: 1, 
    scale: 1,
    transition: transitions.spring
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: transitions.fast
  }
};

// 弹性缩放
export const scaleInBouncy: Variants = {
  initial: { 
    opacity: 0, 
    scale: 0.8 
  },
  animate: { 
    opacity: 1, 
    scale: 1,
    transition: transitions.springBouncy
  },
  exit: {
    opacity: 0,
    scale: 0.8,
    transition: transitions.fast
  }
};

// 旋转淡入
export const rotateIn: Variants = {
  initial: { 
    opacity: 0, 
    rotate: -10,
    scale: 0.95
  },
  animate: { 
    opacity: 1, 
    rotate: 0,
    scale: 1,
    transition: transitions.spring
  },
  exit: {
    opacity: 0,
    rotate: 10,
    scale: 0.95,
    transition: transitions.fast
  }
};

// 列表项动画（交错动画）
export const staggerContainer: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1
    }
  },
  exit: {
    transition: {
      staggerChildren: 0.05,
      staggerDirection: -1
    }
  }
};

export const staggerItem: Variants = {
  initial: { 
    opacity: 0, 
    y: 20 
  },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: transitions.normal
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: transitions.fast
  }
};

// 页面过渡动画
export const pageTransition: Variants = {
  initial: { 
    opacity: 0, 
    x: 20 
  },
  animate: { 
    opacity: 1, 
    x: 0,
    transition: {
      duration: 0.4,
      ease: 'easeOut'
    }
  },
  exit: {
    opacity: 0,
    x: -20,
    transition: {
      duration: 0.3,
      ease: 'easeIn'
    }
  }
};

// 模态框动画
export const modalBackdrop: Variants = {
  initial: { 
    opacity: 0 
  },
  animate: { 
    opacity: 1,
    transition: transitions.fast
  },
  exit: {
    opacity: 0,
    transition: transitions.fast
  }
};

export const modalContent: Variants = {
  initial: { 
    opacity: 0, 
    scale: 0.95,
    y: 20
  },
  animate: { 
    opacity: 1, 
    scale: 1,
    y: 0,
    transition: transitions.spring
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: 20,
    transition: transitions.fast
  }
};

// 按钮交互动画
export const buttonHover = {
  scale: 1.05,
  transition: transitions.fast
};

export const buttonTap = {
  scale: 0.95,
  transition: transitions.fast
};

// 卡片交互动画
export const cardHover = {
  y: -4,
  scale: 1.02,
  boxShadow: '0 8px 30px 0 rgba(0, 0, 0, 0.15)',
  transition: transitions.normal
};

// 加载动画
export const loadingSpinner: Variants = {
  animate: {
    rotate: 360,
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: 'linear'
    }
  }
};

export const loadingPulse: Variants = {
  animate: {
    scale: [1, 1.1, 1],
    opacity: [0.7, 1, 0.7],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'easeInOut'
    }
  }
};

// 滚动触发动画
export const scrollReveal: Variants = {
  initial: { 
    opacity: 0, 
    y: 50 
  },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: {
      duration: 0.6,
      ease: 'easeOut'
    }
  }
};

// 数字计数动画
export const countUp = (from: number, to: number, duration: number = 1) => ({
  initial: { value: from },
  animate: { 
    value: to,
    transition: {
      duration,
      ease: 'easeOut'
    }
  }
});

// 进度条动画
export const progressBar: Variants = {
  initial: { 
    scaleX: 0,
    originX: 0
  },
  animate: { 
    scaleX: 1,
    transition: {
      duration: 0.8,
      ease: 'easeOut'
    }
  }
};

// 通知动画
export const toastSlideIn: Variants = {
  initial: { 
    opacity: 0, 
    x: 100,
    scale: 0.95
  },
  animate: { 
    opacity: 1, 
    x: 0,
    scale: 1,
    transition: transitions.spring
  },
  exit: {
    opacity: 0,
    x: 100,
    scale: 0.95,
    transition: transitions.fast
  }
};

// 工具函数：创建延迟动画
export const createDelayedAnimation = (baseVariant: Variants, delay: number): Variants => {
  return {
    ...baseVariant,
    animate: {
      ...baseVariant.animate,
      transition: {
        ...(baseVariant.animate as any)?.transition,
        delay
      }
    }
  };
};

// 工具函数：创建交错动画容器
export const createStaggerContainer = (staggerDelay: number = 0.1, childrenDelay: number = 0.1): Variants => {
  return {
    initial: {},
    animate: {
      transition: {
        staggerChildren: staggerDelay,
        delayChildren: childrenDelay
      }
    },
    exit: {
      transition: {
        staggerChildren: staggerDelay / 2,
        staggerDirection: -1
      }
    }
  };
};