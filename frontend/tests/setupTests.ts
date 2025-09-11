import '@testing-library/jest-dom';

// Polyfill ResizeObserver used by recharts' ResponsiveContainer
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// @ts-ignore
global.ResizeObserver = ResizeObserverMock;
