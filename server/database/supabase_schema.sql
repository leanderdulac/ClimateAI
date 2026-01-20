-- =====================================================
-- ClimateAI Database Schema for Supabase
-- Execute this in Supabase SQL Editor
-- =====================================================

-- Enable UUID extension (usually enabled by default in Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- PROFILES TABLE (extends Supabase Auth users)
-- =====================================================
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    company_name TEXT,
    phone TEXT,
    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'agent', 'underwriter', 'admin')),
    avatar_url TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- LOCATIONS TABLE (for policy locations)
-- =====================================================
CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT DEFAULT 'Brazil',
    postal_code TEXT,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    climate_zone TEXT,
    risk_zone TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- POLICIES TABLE (Insurance Policies)
-- =====================================================
CREATE TABLE IF NOT EXISTS policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    location_id UUID REFERENCES locations(id) ON DELETE SET NULL,
    
    -- Policy Details
    policy_number TEXT UNIQUE NOT NULL,
    policy_type TEXT NOT NULL CHECK (policy_type IN ('crop', 'property', 'livestock', 'parametric', 'comprehensive')),
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'pending', 'active', 'expired', 'cancelled', 'claimed')),
    
    -- Coverage
    coverage_amount DECIMAL(15, 2) NOT NULL,
    deductible DECIMAL(15, 2) DEFAULT 0,
    premium DECIMAL(15, 2) NOT NULL,
    premium_frequency TEXT DEFAULT 'annual' CHECK (premium_frequency IN ('monthly', 'quarterly', 'semi-annual', 'annual')),
    
    -- Dates
    effective_date DATE NOT NULL,
    expiration_date DATE NOT NULL,
    
    -- Risk Assessment
    risk_score DECIMAL(5, 2),
    risk_level TEXT CHECK (risk_level IN ('very_low', 'low', 'medium', 'high', 'very_high')),
    climate_risk_factor DECIMAL(5, 4),
    
    -- Pricing Details
    base_premium DECIMAL(15, 2),
    loading_factor DECIMAL(5, 4),
    discount_factor DECIMAL(5, 4),
    pricing_model TEXT,
    pricing_details JSONB DEFAULT '{}',
    
    -- Metadata
    notes TEXT,
    documents JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- CLAIMS TABLE (Insurance Claims / Sinistros)
-- =====================================================
CREATE TABLE IF NOT EXISTS claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    
    -- Claim Details
    claim_number TEXT UNIQUE NOT NULL,
    claim_type TEXT NOT NULL CHECK (claim_type IN ('weather_damage', 'drought', 'flood', 'hail', 'frost', 'fire', 'pest', 'disease', 'other')),
    status TEXT DEFAULT 'reported' CHECK (status IN ('reported', 'under_review', 'approved', 'partially_approved', 'denied', 'paid', 'closed')),
    
    -- Event Details
    event_date DATE NOT NULL,
    event_description TEXT,
    event_location_lat DECIMAL(10, 8),
    event_location_lng DECIMAL(11, 8),
    
    -- Financial
    claimed_amount DECIMAL(15, 2) NOT NULL,
    approved_amount DECIMAL(15, 2),
    paid_amount DECIMAL(15, 2),
    
    -- Assessment
    adjuster_id UUID REFERENCES profiles(id),
    assessment_date DATE,
    assessment_notes TEXT,
    damage_percentage DECIMAL(5, 2),
    
    -- Documents & Evidence
    documents JSONB DEFAULT '[]',
    photos JSONB DEFAULT '[]',
    weather_data JSONB DEFAULT '{}',
    
    -- Dates
    reported_at TIMESTAMPTZ DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- CLIMATE_DATA TABLE (Historical climate records)
-- =====================================================
CREATE TABLE IF NOT EXISTS climate_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_id UUID REFERENCES locations(id) ON DELETE CASCADE,
    
    -- Location (for records without location_id)
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    
    -- Date
    recorded_date DATE NOT NULL,
    
    -- Weather Data
    temperature_avg DECIMAL(5, 2),
    temperature_max DECIMAL(5, 2),
    temperature_min DECIMAL(5, 2),
    precipitation DECIMAL(8, 2),
    humidity DECIMAL(5, 2),
    wind_speed DECIMAL(6, 2),
    wind_direction DECIMAL(5, 2),
    pressure DECIMAL(7, 2),
    uv_index DECIMAL(4, 2),
    
    -- Extreme Events
    is_extreme_event BOOLEAN DEFAULT FALSE,
    extreme_event_type TEXT,
    
    -- Source
    source TEXT DEFAULT 'openmeteo',
    raw_data JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- RISK_ASSESSMENTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS risk_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    location_id UUID REFERENCES locations(id) ON DELETE SET NULL,
    
    -- Assessment Details
    assessment_type TEXT NOT NULL CHECK (assessment_type IN ('initial', 'renewal', 'claim', 'periodic')),
    assessment_date TIMESTAMPTZ DEFAULT NOW(),
    
    -- Risk Scores
    overall_risk_score DECIMAL(5, 2),
    climate_risk_score DECIMAL(5, 2),
    physical_risk_score DECIMAL(5, 2),
    transition_risk_score DECIMAL(5, 2),
    concentration_risk_score DECIMAL(5, 2),
    
    -- Model Results
    model_used TEXT,
    model_version TEXT,
    confidence_interval JSONB,
    
    -- Recommendations
    risk_level TEXT CHECK (risk_level IN ('very_low', 'low', 'medium', 'high', 'very_high')),
    recommended_premium DECIMAL(15, 2),
    recommendations JSONB DEFAULT '[]',
    
    -- Raw Data
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- PRICING_HISTORY TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS pricing_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID REFERENCES policies(id) ON DELETE CASCADE,
    
    -- Pricing Details
    calculation_date TIMESTAMPTZ DEFAULT NOW(),
    pricing_model TEXT NOT NULL,
    
    -- Premium Components
    base_premium DECIMAL(15, 2),
    risk_loading DECIMAL(15, 2),
    expense_loading DECIMAL(15, 2),
    profit_margin DECIMAL(15, 2),
    discounts DECIMAL(15, 2),
    final_premium DECIMAL(15, 2) NOT NULL,
    
    -- Model Details
    model_weights JSONB DEFAULT '{}',
    model_results JSONB DEFAULT '{}',
    confidence_level DECIMAL(5, 4),
    
    -- Metadata
    calculated_by UUID REFERENCES profiles(id),
    notes TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- AUDIT_LOG TABLE (for compliance)
-- =====================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    
    -- Action Details
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    
    -- Data
    old_data JSONB,
    new_data JSONB,
    
    -- Context
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- INDEXES for Performance
-- =====================================================

-- Policies indexes
CREATE INDEX IF NOT EXISTS idx_policies_user_id ON policies(user_id);
CREATE INDEX IF NOT EXISTS idx_policies_location_id ON policies(location_id);
CREATE INDEX IF NOT EXISTS idx_policies_status ON policies(status);
CREATE INDEX IF NOT EXISTS idx_policies_effective_date ON policies(effective_date);
CREATE INDEX IF NOT EXISTS idx_policies_policy_number ON policies(policy_number);

-- Claims indexes
CREATE INDEX IF NOT EXISTS idx_claims_policy_id ON claims(policy_id);
CREATE INDEX IF NOT EXISTS idx_claims_user_id ON claims(user_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
CREATE INDEX IF NOT EXISTS idx_claims_event_date ON claims(event_date);
CREATE INDEX IF NOT EXISTS idx_claims_claim_number ON claims(claim_number);

-- Climate data indexes
CREATE INDEX IF NOT EXISTS idx_climate_data_location_id ON climate_data(location_id);
CREATE INDEX IF NOT EXISTS idx_climate_data_recorded_date ON climate_data(recorded_date);
CREATE INDEX IF NOT EXISTS idx_climate_data_coords ON climate_data(latitude, longitude);

-- Risk assessments indexes
CREATE INDEX IF NOT EXISTS idx_risk_assessments_policy_id ON risk_assessments(policy_id);
CREATE INDEX IF NOT EXISTS idx_risk_assessments_date ON risk_assessments(assessment_date);

-- Pricing history indexes
CREATE INDEX IF NOT EXISTS idx_pricing_history_policy_id ON pricing_history(policy_id);
CREATE INDEX IF NOT EXISTS idx_pricing_history_date ON pricing_history(calculation_date);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) Policies
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE climate_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE pricing_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can only see/edit their own profile
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);
    
CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

-- Policies: Users can see their own policies, admins can see all
CREATE POLICY "Users can view own policies" ON policies
    FOR SELECT USING (
        auth.uid() = user_id OR 
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin', 'underwriter'))
    );

CREATE POLICY "Users can create policies" ON policies
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own policies" ON policies
    FOR UPDATE USING (
        auth.uid() = user_id OR 
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin', 'underwriter'))
    );

-- Claims: Users can see claims for their policies
CREATE POLICY "Users can view own claims" ON claims
    FOR SELECT USING (
        auth.uid() = user_id OR
        EXISTS (SELECT 1 FROM policies WHERE policies.id = claims.policy_id AND policies.user_id = auth.uid()) OR
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin', 'underwriter', 'agent'))
    );

CREATE POLICY "Users can create claims for own policies" ON claims
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM policies WHERE policies.id = policy_id AND policies.user_id = auth.uid())
    );

-- Climate data: Public read access
CREATE POLICY "Anyone can view climate data" ON climate_data
    FOR SELECT USING (true);

-- Locations: Public read, authenticated write
CREATE POLICY "Anyone can view locations" ON locations
    FOR SELECT USING (true);

CREATE POLICY "Authenticated users can create locations" ON locations
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- Risk assessments: Users can see assessments for their policies
CREATE POLICY "Users can view own risk assessments" ON risk_assessments
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM policies WHERE policies.id = policy_id AND policies.user_id = auth.uid()) OR
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin', 'underwriter'))
    );

-- Pricing history: Users can see pricing for their policies
CREATE POLICY "Users can view own pricing history" ON pricing_history
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM policies WHERE policies.id = policy_id AND policies.user_id = auth.uid()) OR
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role IN ('admin', 'underwriter'))
    );

-- Audit log: Only admins can view
CREATE POLICY "Only admins can view audit log" ON audit_log
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
    );

-- =====================================================
-- FUNCTIONS & TRIGGERS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_locations_updated_at
    BEFORE UPDATE ON locations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_policies_updated_at
    BEFORE UPDATE ON policies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_claims_updated_at
    BEFORE UPDATE ON claims
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to automatically create profile on user signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile on signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION handle_new_user();

-- Function to generate policy number
CREATE OR REPLACE FUNCTION generate_policy_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.policy_number IS NULL OR NEW.policy_number = '' THEN
        NEW.policy_number := 'POL-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || SUBSTRING(NEW.id::TEXT, 1, 8);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_policy_number
    BEFORE INSERT ON policies
    FOR EACH ROW
    EXECUTE FUNCTION generate_policy_number();

-- Function to generate claim number
CREATE OR REPLACE FUNCTION generate_claim_number()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.claim_number IS NULL OR NEW.claim_number = '' THEN
        NEW.claim_number := 'CLM-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || SUBSTRING(NEW.id::TEXT, 1, 8);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_claim_number
    BEFORE INSERT ON claims
    FOR EACH ROW
    EXECUTE FUNCTION generate_claim_number();

-- =====================================================
-- DONE! Schema created successfully
-- =====================================================
