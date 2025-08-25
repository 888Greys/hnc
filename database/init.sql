-- HNC Legal Questionnaire Database Initialization
-- This script sets up the initial database schema and test data

-- Create database if not exists (handled by Docker environment variables)
-- CREATE DATABASE IF NOT EXISTS hnc_legal;

-- Connect to the database
\c hnc_legal;

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'lawyer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on username and email
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Create clients table
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    marital_status VARCHAR(50),
    spouse_name VARCHAR(200),
    spouse_id VARCHAR(50),
    children TEXT,
    assets JSONB,
    liabilities TEXT,
    income_sources TEXT,
    economic_standing VARCHAR(100),
    distribution_prefs TEXT,
    objective VARCHAR(100),
    objective_details TEXT,
    lawyer_notes TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for clients
CREATE INDEX IF NOT EXISTS idx_clients_client_id ON clients(client_id);
CREATE INDEX IF NOT EXISTS idx_clients_full_name ON clients(full_name);
CREATE INDEX IF NOT EXISTS idx_clients_created_by ON clients(created_by);
CREATE INDEX IF NOT EXISTS idx_clients_created_at ON clients(created_at);

-- Create AI proposals table
CREATE TABLE IF NOT EXISTS ai_proposals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id),
    suggestion TEXT NOT NULL,
    legal_references JSONB,
    consequences JSONB,
    next_steps JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for AI proposals
CREATE INDEX IF NOT EXISTS idx_ai_proposals_client_id ON ai_proposals(client_id);
CREATE INDEX IF NOT EXISTS idx_ai_proposals_created_at ON ai_proposals(created_at);

-- Create user sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Create indexes for sessions
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for audit logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, full_name, password_hash, role) 
VALUES (
    'admin',
    'admin@hnc-legal.com',
    'System Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeOjNdUfcZGZU8.VW', -- admin123
    'admin'
) ON CONFLICT (username) DO NOTHING;

-- Insert sample lawyer user (password: lawyer123)
INSERT INTO users (username, email, full_name, password_hash, role) 
VALUES (
    'lawyer1',
    'lawyer@hnc-legal.com',
    'John Doe, Esq.',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPDVn4vJu', -- lawyer123
    'lawyer'
) ON CONFLICT (username) DO NOTHING;

-- Create sample client data
INSERT INTO clients (
    client_id, full_name, marital_status, spouse_name, children,
    assets, economic_standing, objective, objective_details,
    created_by
) 
SELECT 
    'client_sample_001',
    'Jane Smith',
    'Married',
    'John Smith',
    '2 children: Mary (15), Paul (12)',
    '{"assets": [{"type": "Real Estate", "description": "Family home", "value": 8000000}, {"type": "Savings", "description": "Bank savings", "value": 2000000}]}'::jsonb,
    'Upper middle class',
    'Estate Planning',
    'Create comprehensive will and trust for children''s education',
    users.id
FROM users WHERE username = 'lawyer1'
ON CONFLICT (client_id) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hnc_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hnc_user;

-- Create view for client summary
CREATE OR REPLACE VIEW client_summary AS
SELECT 
    c.client_id,
    c.full_name,
    c.marital_status,
    c.economic_standing,
    c.objective,
    u.full_name as created_by_name,
    c.created_at,
    c.updated_at,
    COUNT(ap.id) as proposal_count
FROM clients c
LEFT JOIN users u ON c.created_by = u.id
LEFT JOIN ai_proposals ap ON c.id = ap.client_id
GROUP BY c.id, u.full_name;

-- Log initialization completion
INSERT INTO audit_logs (user_id, action, resource_type, details) 
VALUES (
    (SELECT id FROM users WHERE username = 'admin'),
    'SYSTEM_INIT',
    'DATABASE',
    '{"message": "Database initialized successfully", "timestamp": "' || CURRENT_TIMESTAMP || '"}'
);

-- Print success message
\echo 'HNC Legal Database initialized successfully!'
\echo 'Default users created:'
\echo '  - admin (password: admin123)'
\echo '  - lawyer1 (password: lawyer123)'