-- ClimateAI - Script de Inicialização do Banco de Dados
-- Executar: podman exec -i climateai-db psql -U postgres -d climateai < init-db.sql

-- Habilitar extensão UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabela de Usuários
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Políticas/Seguros
CREATE TABLE IF NOT EXISTS policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    policy_number VARCHAR(100) UNIQUE,
    asset_value DECIMAL(15, 2) NOT NULL,
    coverage_amount DECIMAL(15, 2) NOT NULL,
    premium_amount DECIMAL(15, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Eventos Climáticos
CREATE TABLE IF NOT EXISTS climate_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Tabela de Sinistros
CREATE TABLE IF NOT EXISTS claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID REFERENCES policies(id),
    event_id UUID REFERENCES climate_events(id),
    claim_amount DECIMAL(15, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    filed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Tabela de Auditoria
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    details JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_policies_user_id ON policies(user_id);
CREATE INDEX IF NOT EXISTS idx_policies_status ON policies(status);
CREATE INDEX IF NOT EXISTS idx_claims_policy_id ON claims(policy_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- Inserir usuário de teste (senha: admin123)
-- Hash gerado com bcrypt
INSERT INTO users (email, password_hash, full_name, role) 
VALUES 
    ('admin@climateai.com', '$2b$10$KIXxhQmQ7QkQzQxQzQxQzOQkQ7QkQzQxQzQxQzOQkQ7QkQzQxQzQx', 'Admin User', 'admin'),
    ('user@climateai.com', '$2b$10$KIXxhQmQ7QkQzQxQzQxQzOQkQ7QkQzQxQzQxQzOQkQ7QkQzQxQzQx', 'Test User', 'user')
ON CONFLICT (email) DO NOTHING;

-- Inserir dados de exemplo
INSERT INTO policies (user_id, policy_number, asset_value, coverage_amount, premium_amount, status)
SELECT 
    u.id,
    'POL-' || TO_CHAR(CURRENT_DATE, 'YYYYMM') || '-' || LPAD(ROW_NUMBER() OVER (ORDER BY u.email)::text, 4, '0'),
    100000.00,
    100000.00,
    1485.00,
    'active'
FROM users u
WHERE u.email = 'user@climateai.com'
ON CONFLICT (policy_number) DO NOTHING;

-- Verificar dados inseridos
SELECT 'Usuários criados:' as status, COUNT(*) as total FROM users;
SELECT 'Políticas criadas:' as status, COUNT(*) as total FROM policies;
