import { render, screen } from '@testing-library/react';
import { SignalList } from '../../src/components/signals/SignalList';
import { TradingSignal } from '../../src/components/signals/SignalCard';

function makeSignal(id: string, symbol: string, prob: number): TradingSignal {
  const now = new Date();
  const later = new Date(now.getTime() + 10 * 60 * 1000);
  return {
    id,
    timestamp: now.toISOString(),
    symbol,
    direction: prob > 0.5 ? 'UP' : 'DOWN',
    predicted_probability: prob,
    confidence_level: prob > 0.7 ? 'HIGH' : 'LOW',
    expiry_time: later.toISOString(),
  };
}

describe('SignalList', () => {
  it('renders a list of signals and empty state', () => {
    const signals: TradingSignal[] = [
      makeSignal('1', 'ETHUSDT', 0.62),
      makeSignal('2', 'BNBUSDT', 0.48),
    ];

    const { rerender } = render(<SignalList signals={signals} />);

    expect(screen.getByText('ETHUSDT')).toBeInTheDocument();
    expect(screen.getByText('BNBUSDT')).toBeInTheDocument();

    // Empty state
    rerender(<SignalList signals={[]} />);
    expect(screen.getByText('No signals to display.')).toBeInTheDocument();
  });
});

