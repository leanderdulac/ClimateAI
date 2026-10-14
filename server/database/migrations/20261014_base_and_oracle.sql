-- =========================================================================
-- ClimateWise Supabase Migration: Base (Coinbase L2) & Enhanced Oracle
-- Date: 2026-10-14
-- Adds Base Sepolia/Mainnet support, ERC-3525 Parametric Policies,
-- Multi-source Oracle Triangulation, and Canonical SHA-256 Audit Records.
-- =========================================================================

-- 1. Extend policies table for On-Chain RWA Tokenization
ALTER TABLE IF EXISTS policies
    ADD COLUMN IF NOT EXISTS blockchain_network TEXT DEFAULT 'base_sepolia',
    ADD COLUMN IF NOT EXISTS blockchain_chain_id INTEGER DEFAULT 84532,
    ADD COLUMN IF NOT EXISTS blockchain_contract TEXT DEFAULT '0x01dD68040B926Fd4938cD43Ae3c88758874DD0D0',
    ADD COLUMN IF NOT EXISTS blockchain_token_id INTEGER,
    ADD COLUMN IF NOT EXISTS blockchain_slot INTEGER,
    ADD COLUMN IF NOT EXISTS blockchain_mint_tx_hash TEXT,
    ADD COLUMN IF NOT EXISTS blockchain_payout_tx_hash TEXT,
    ADD COLUMN IF NOT EXISTS blockchain_explorer_url TEXT;

-- 2. Extend oracle_events / climate_events for Cryptographic Evidence & Triangulation
ALTER TABLE IF EXISTS oracle_events
    ADD COLUMN IF NOT EXISTS evidence_hash TEXT,
    ADD COLUMN IF NOT EXISTS evidence_json JSONB DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS consensus_proof JSONB DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS triangulation_sources JSONB DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS onchain_tx_hash TEXT,
    ADD COLUMN IF NOT EXISTS onchain_verified BOOLEAN DEFAULT FALSE;

-- 3. Extend blockchain_transactions table with Base L2 metadata
ALTER TABLE IF EXISTS blockchain_transactions
    ADD COLUMN IF NOT EXISTS network TEXT DEFAULT 'base_sepolia',
    ADD COLUMN IF NOT EXISTS chain_id INTEGER DEFAULT 84532,
    ADD COLUMN IF NOT EXISTS contract_address TEXT,
    ADD COLUMN IF NOT EXISTS token_id INTEGER,
    ADD COLUMN IF NOT EXISTS slot INTEGER,
    ADD COLUMN IF NOT EXISTS evidence_hash TEXT,
    ADD COLUMN IF NOT EXISTS gas_used INTEGER;

-- 4. Create indexes for quick lookups
CREATE INDEX IF NOT EXISTS idx_policies_blockchain_token_id ON policies(blockchain_token_id);
CREATE INDEX IF NOT EXISTS idx_policies_blockchain_contract ON policies(blockchain_contract);
CREATE INDEX IF NOT EXISTS idx_blockchain_tx_network_hash ON blockchain_transactions(network, tx_hash);
CREATE INDEX IF NOT EXISTS idx_oracle_events_evidence_hash ON oracle_events(evidence_hash);

-- 5. Seed Real On-Chain Records from Live Base Sepolia Deployment
INSERT INTO blockchain_transactions (
    tx_hash,
    network,
    chain_id,
    contract_address,
    token_id,
    from_address,
    to_address,
    amount,
    gas_used,
    status,
    message,
    explorer_url
) VALUES
(
    '0xc2e16c75a347eb5c567ac1b5663be8da944a23c580ecda95026f723f4cffe4f1',
    'base_sepolia',
    84532,
    '0x01dD68040B926Fd4938cD43Ae3c88758874DD0D0',
    NULL,
    '0x97e7Ba06ecaF6A2787d5C72C995C30eE4f893369',
    '0x01dD68040B926Fd4938cD43Ae3c88758874DD0D0',
    0.0,
    3125400,
    'confirmed',
    'Contract Deployment: ClimatePolicy.sol (ERC-3525 Parametric Engine)',
    'https://sepolia.basescan.org/address/0x01dD68040B926Fd4938cD43Ae3c88758874DD0D0'
),
(
    '0x1d4fa54cb10ac96a307eea17d178165e908efd53d828192e4926db66b13a3968',
    'base_sepolia',
    84532,
    '0x01dD68040B926Fd4938cD43Ae3c88758874DD0D0',
    1,
    '0x97e7Ba06ecaF6A2787d5C72C995C30eE4f893369',
    '0x97e7Ba06ecaF6A2787d5C72C995C30eE4f893369',
    108150.69,
    109663,
    'confirmed',
    'Parametric Policy Token #1 Minted: Coverage R$ 108.150,69 (Slot 20261014)',
    'https://sepolia.basescan.org/tx/1d4fa54cb10ac96a307eea17d178165e908efd53d828192e4926db66b13a3968'
),
(
    '0x66f4d5c044e6598235f580b68bb8b361bf9ff7f9fc187e2da5cd1200cf645dcb',
    'base_sepolia',
    84532,
    '0x01dD68040B926Fd4938cD43Ae3c88758874DD0D0',
    1,
    '0x97e7Ba06ecaF6A2787d5C72C995C30eE4f893369',
    '0x97e7Ba06ecaF6A2787d5C72C995C30eE4f893369',
    54075.34,
    40345,
    'confirmed',
    'Oracle Settlement #1: 50% Parametric Payout with SHA-256 Proof (0x26244c37af3bea013d806abe5a9475cbe06e8a73bc5e0ca72caa4a16b6b66b69)',
    'https://sepolia.basescan.org/tx/66f4d5c044e6598235f580b68bb8b361bf9ff7f9fc187e2da5cd1200cf645dcb'
),
(
    '0x5f4c8c66442911db0e0fec95b2bc531060bcd7075f89370c9eba119294eb1200',
    'base_sepolia',
    84532,
    '0x01dD68040B926Fd4938cD43Ae3c88758874DD0D0',
    2,
    '0x97e7Ba06ecaF6A2787d5C72C995C30eE4f893369',
    '0x97e7Ba06ecaF6A2787d5C72C995C30eE4f893369',
    108150.69,
    109663,
    'confirmed',
    'Parametric Policy Token #2 Minted: BaseService Integration Test',
    'https://sepolia.basescan.org/tx/5f4c8c66442911db0e0fec95b2bc531060bcd7075f89370c9eba119294eb1200'
),
(
    '0x458d18cd9d9e2f8460dc122d09b7b8de4e6672c7977a729bbfe22be4d8da03c3',
    'base_sepolia',
    84532,
    '0x01dD68040B926Fd4938cD43Ae3c88758874DD0D0',
    2,
    '0x97e7Ba06ecaF6A2787d5C72C995C30eE4f893369',
    '0x97e7Ba06ecaF6A2787d5C72C995C30eE4f893369',
    54075.34,
    40345,
    'confirmed',
    'Oracle Settlement #2: Automated Settlement via BaseService with M-of-N Consensus Proof',
    'https://sepolia.basescan.org/tx/458d18cd9d9e2f8460dc122d09b7b8de4e6672c7977a729bbfe22be4d8da03c3'
)
ON CONFLICT (tx_hash) DO NOTHING;
