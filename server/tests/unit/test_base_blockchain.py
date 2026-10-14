"""
Unit Tests for Base Blockchain Integration (Coinbase Ethereum L2):
- BaseConfig validation (Chain IDs 84532 & 8453, RPC, BaseScan explorers)
- BaseService Web3 RPC connectivity and live block fetching
- EIP-1559 gas price retrieval
- Policy token minting on Base (ERC-3525)
- Parametric Oracle Payout execution with proof (triggerPayoutWithProof)
- High-level ClimatePolicyBaseService workflow
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from blockchain.base.config import BaseConfig
from blockchain.base.base_service import BaseService
from blockchain.base.climate_policy_service import ClimatePolicyBaseService


@pytest.fixture
def base_config():
    return BaseConfig(NETWORK="sepolia")


@pytest.fixture
def base_service(base_config):
    return BaseService(config=base_config)


@pytest.fixture
def policy_service(base_service):
    return ClimatePolicyBaseService(base_service=base_service)


def test_base_config_settings(base_config):
    """Test Base network configuration parameters."""
    assert base_config.NETWORK == "sepolia"
    assert base_config.chain_id == 84532
    assert "sepolia.base.org" in base_config.rpc_url
    assert "sepolia.basescan.org" in base_config.explorer_url
    assert base_config.is_testnet is True

    # Mainnet checks
    mainnet_cfg = BaseConfig(NETWORK="mainnet")
    assert mainnet_cfg.chain_id == 8453
    assert "mainnet.base.org" in mainnet_cfg.rpc_url
    assert "basescan.org" in mainnet_cfg.explorer_url
    assert mainnet_cfg.is_testnet is False


def test_base_service_connectivity_and_blocks(base_service):
    """Verify live/simulated RPC connectivity and block heights."""
    # When connected to public testnet
    status = base_service.get_status()
    assert status["blockchain"] == "Base (Coinbase Ethereum L2)"
    assert status["chain_id"] == 84532
    assert status["network"] == "sepolia"

    if base_service.is_connected():
        block_num = base_service.get_block_number()
        assert block_num > 0
        print(f"Connected to Base Sepolia at block height: {block_num}")


def test_base_service_gas_price(base_service):
    """Test gas price retrieval on Base L2."""
    gas_info = base_service.get_gas_price()
    assert "gas_price_gwei" in gas_info
    assert gas_info["network"] == "sepolia"


def test_base_service_balance_query(base_service):
    """Test ETH and USDC balance queries."""
    sample_address = "0x0000000000000000000000000000000000000001"
    bal = base_service.get_balance(sample_address)
    assert "eth" in bal
    assert "usdc" in bal
    assert bal["address"].lower() == sample_address.lower()


def test_base_service_mint_policy(base_service):
    """Test mintPolicy call on Base Layer-2."""
    beneficiary = "0x1234567890123456789012345678901234567890"
    slot = 1001  # Flood risk
    coverage_cents = 5000000  # R$ 50,000.00

    result = base_service.mint_policy(
        to_address=beneficiary,
        slot=slot,
        coverage_amount_cents=coverage_cents,
    )
    assert result.success is True
    assert result.tx_hash.startswith("0x")
    assert result.chain_id == 84532
    assert "sepolia.basescan.org/tx/" in result.explorer_url
    assert result.token_id is not None


def test_base_service_trigger_payout_with_proof(base_service):
    """Test triggerPayoutWithProof with cryptographic evidence hash on Base."""
    # Mint a valid token first
    mint_res = base_service.mint_policy(
        to_address="0x1234567890123456789012345678901234567890",
        slot=1001,
        coverage_amount_cents=5000000,
    )
    token_id = mint_res.token_id or 1
    payout_cents = 2500000  # R$ 25,000.00
    evidence_hash = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    result = base_service.trigger_payout_with_proof(
        token_id=token_id,
        payout_amount_cents=payout_cents,
        evidence_hash=evidence_hash,
    )
    assert result.success is True
    assert result.tx_hash.startswith("0x")
    assert result.evidence_hash == evidence_hash
    assert result.token_id == token_id
    assert "sepolia.basescan.org/tx/" in result.explorer_url


def test_climate_policy_base_service_workflow(policy_service):
    """Test end-to-end tokenization and settlement workflow on Base."""
    farmer_wallet = "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
    coverage_brl = 150000.0

    # 1. Tokenize approved policy
    policy_record = policy_service.tokenize_policy(
        beneficiary_address=farmer_wallet,
        coverage_amount_brl=coverage_brl,
        disaster_type="flood",
        latitude=-23.55,
        longitude=-46.63,
    )
    assert policy_record.beneficiary == farmer_wallet
    assert policy_record.coverage_value_brl == 150000.0
    assert policy_record.risk_slot == 1001
    assert policy_record.status == "ACTIVE"
    assert policy_record.token_id in policy_service.minted_policies

    # 2. Settle 100% parametric payout with proof
    proof_hash = "0x11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff"
    settle_tx = policy_service.settle_policy_payout(
        token_id=policy_record.token_id,
        payout_percentage=1.0,
        evidence_hash=proof_hash,
    )
    assert settle_tx.success is True
    assert settle_tx.evidence_hash == proof_hash
    assert policy_record.status == "PAID_OUT"
