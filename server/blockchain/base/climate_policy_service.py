"""
Climate Policy Service on Base Blockchain
Orchestrates the tokenization (RWA) of approved insurance policies into ERC-3525 tokens on Base.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from blockchain.base.base_service import BaseService, BaseTransactionResult, get_base_service

logger = logging.getLogger(__name__)


@dataclass
class TokenizedPolicyRecord:
    """Represents a minted parametric policy token on Base."""
    token_id: int
    tx_hash: str
    beneficiary: str
    coverage_value_brl: float
    coverage_cents: int
    risk_slot: int
    chain_id: int
    network: str
    explorer_url: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "ACTIVE"


class ClimatePolicyBaseService:
    """
    Business service bridging ClimateWise actuarial risk engine to Base Layer-2 tokenization.
    """

    def __init__(self, base_service: Optional[BaseService] = None):
        self.base = base_service or get_base_service()
        self.minted_policies: Dict[int, TokenizedPolicyRecord] = {}

    def tokenize_policy(
        self,
        beneficiary_address: str,
        coverage_amount_brl: float,
        disaster_type: str = "flood",
        latitude: float = -23.55,
        longitude: float = -46.63,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TokenizedPolicyRecord:
        """
        Mints a semi-fungible policy token (ERC-3525) on Base representing a parametric insurance contract.
        
        Args:
            beneficiary_address: EVM address of the policyholder (farmer / company)
            coverage_amount_brl: Insured coverage in BRL
            disaster_type: e.g. flood, drought, windstorm
            latitude/longitude: Geographic coordinates of the insured asset
            metadata: Supplemental actuarial data, EVT metrics, or IPFS links
        """
        # Convert BRL to integer cents
        coverage_cents = int(coverage_amount_brl * 100)

        # Slot encodes the risk class (e.g., 1001 for Flood SP, 2001 for Drought Cerrado)
        risk_slots = {
            "flood": 1001,
            "drought": 2001,
            "frost": 3001,
            "windstorm": 4001,
            "general_climate": 5001,
        }
        slot = risk_slots.get(disaster_type.lower(), 5001)

        # Call Base L2 Service
        tx_result = self.base.mint_policy(
            to_address=beneficiary_address,
            slot=slot,
            coverage_amount_cents=coverage_cents,
        )

        token_id = tx_result.token_id or int(datetime.now().timestamp())
        record = TokenizedPolicyRecord(
            token_id=token_id,
            tx_hash=tx_result.tx_hash,
            beneficiary=beneficiary_address,
            coverage_value_brl=coverage_amount_brl,
            coverage_cents=coverage_cents,
            risk_slot=slot,
            chain_id=tx_result.chain_id,
            network=tx_result.network,
            explorer_url=tx_result.explorer_url,
        )

        self.minted_policies[token_id] = record
        logger.info(
            "✅ Policy tokenized on Base: Token ID #%d | Coverage: R$ %.2f | Tx: %s",
            token_id,
            coverage_amount_brl,
            tx_result.tx_hash,
        )
        return record

    def settle_policy_payout(
        self,
        token_id: int,
        payout_percentage: float,
        evidence_hash: str,
    ) -> BaseTransactionResult:
        """
        Executes parametric settlement on Base when the Oracle detects a corroborated climate breach.
        """
        policy = self.minted_policies.get(token_id)
        if policy:
            payout_cents = int(policy.coverage_cents * min(max(payout_percentage, 0.0), 1.0))
        else:
            payout_cents = 100_000  # Default fallback amount

        tx_result = self.base.trigger_payout_with_proof(
            token_id=token_id,
            payout_amount_cents=payout_cents,
            evidence_hash=evidence_hash,
        )

        if policy:
            policy.status = "PAID_OUT" if payout_percentage >= 1.0 else "PARTIALLY_SETTLED"

        return tx_result


_policy_base_service: Optional[ClimatePolicyBaseService] = None


def get_climate_policy_base_service() -> ClimatePolicyBaseService:
    global _policy_base_service
    if _policy_base_service is None:
        _policy_base_service = ClimatePolicyBaseService()
    return _policy_base_service
