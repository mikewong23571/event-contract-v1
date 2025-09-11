import { render, screen } from '@testing-library/react';
import { SignalCard, TradingSignal } from '../../src/components/signals/SignalCard';

function makeSignal(overrides: Partial<TradingSignal> = {}): TradingSignal {
  const now = new Date();
  const later = new Date(now.getTime() + 5 * 60 * 1000);
  return {
    id: 'sig-1',
    timestamp: now.toISOString(),
    symbol: 'BTCUSDT',
    direction: 'UP',
    predicted_probability: 0.73,
    confidence_level: 'HIGH',
    expiry_time: later.toISOString(),
    ...overrides,
  };
}

describe('SignalCard', () => {
  it('renders symbol, direction and probability', () => {
    const signal = makeSignal();
    render(<SignalCard signal={signal} />);

    expect(screen.getByText('BTCUSDT')).toBeInTheDocument();
    expect(screen.getByLabelText('Direction UP')).toBeInTheDocument();
    // Probability percentage text
    expect(screen.getByText('73%')).toBeInTheDocument();
  });

  it('renders confidence badge', () => {
    const signal = makeSignal({ confidence_level: 'MEDIUM' });
    render(<SignalCard signal={signal} />);
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();
  });
});
