-- T081: Database seeding for development data

-- Minimal seed data to validate schema and enable local development

-- Risk parameters for a demo user
INSERT INTO trading.risk_parameters (
    user_id, max_bet_size, max_daily_bets, max_parallel_positions,
    min_probability_edge, frequency_limit_minutes, max_daily_loss
) VALUES (
    'demo_user', 50.00, 20, 3, 0.05, 2, 200.00
) ON CONFLICT DO NOTHING;

-- One example event contract (ACTIVE)
INSERT INTO trading.event_contracts (
    contract_id, symbol, strike_price, expiry_time, payout_ratio,
    implied_probability, status
) VALUES (
    'BNCEVT-0001', 'BTCUSDT', 62000.00, NOW() + INTERVAL '10 minutes',
    0.80, 0.4444, 'ACTIVE'
) ON CONFLICT DO NOTHING;

