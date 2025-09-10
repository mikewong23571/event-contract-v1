-- Event Contract Trading System
-- Initial database schema setup

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS trading;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Set default search path
ALTER DATABASE event_contract_db SET search_path TO trading, public;

-- Create basic tables (will be expanded in later tasks)
CREATE TABLE IF NOT EXISTS trading.system_info (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    initialized_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert initial system info
INSERT INTO trading.system_info (version) 
VALUES ('0.1.0') 
ON CONFLICT DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_system_info_version ON trading.system_info(version);

-- Grant permissions (will be expanded with specific tables)
GRANT USAGE ON SCHEMA trading TO event_contract_user;
GRANT USAGE ON SCHEMA analytics TO event_contract_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA trading TO event_contract_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analytics TO event_contract_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA trading TO event_contract_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA analytics TO event_contract_user;