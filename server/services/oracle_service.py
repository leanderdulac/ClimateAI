"""
Oracle Cloud Function Service — Settlement Trigger
Monitors severity scores from Vertex AI and triggers automatic payouts
on the ERC-3525 smart contract when severity thresholds are breached.

Architecture:
  Vertex AI (Score) → Oracle → KMS Sign → Blockchain (triggerPayout)

Designed for deployment as a GCP Cloud Function or as a FastAPI background task.
"""

import logging
import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SeverityEvent:
    """Represents a climate severity event detected by Vertex AI."""
    token_id: int
    latitude: float
    longitude: float
    severity_score: float  # 1.0 to 5.0
    ndvi: float
    soil_moisture: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "vertex_ai"
    consensus_votes: int = 0
    consensus_required: int = 1


class OracleService:
    """
    Climate Oracle Service.
    Bridges off-chain climate intelligence with on-chain settlement contracts.

    Modes:
        - LOCAL: Simulates oracle logic without blockchain interaction
        - TESTNET: Signs and sends real transactions via KMS to testnet
        - MAINNET: Production mode with multi-oracle consensus
    """

    # Severity threshold for triggering automatic payout (Severity >= 3)
    SEVERITY_THRESHOLD = 3.0
    # Minimum confidence for triggering payout
    MIN_CONFIDENCE = 0.85

    def __init__(self, kms_signer=None, web3_provider: Optional[str] = None):
        self.mode = os.getenv("ORACLE_MODE", "LOCAL").upper()
        self.kms_signer = kms_signer
        self.contract_address = os.getenv("CLIMATE_POLICY_CONTRACT", None)
        self.pending_events: List[SeverityEvent] = []
        self.processed_events: List[Dict[str, Any]] = []
        self.w3 = None

        if web3_provider or os.getenv("WEB3_PROVIDER_URL"):
            self._init_web3(web3_provider or os.getenv("WEB3_PROVIDER_URL"))

        logger.info(f"Oracle Service initialized in {self.mode} mode")

    def _init_web3(self, provider_url: str):
        """Initialize Web3 connection (Blockchain Node Engine or public RPC)."""
        try:
            from web3 import Web3
            self.w3 = Web3(Web3.HTTPProvider(provider_url))
            if self.w3.is_connected():
                logger.info(f"✅ Oracle connected to blockchain: {provider_url}")
            else:
                logger.warning(f"⚠️ Oracle could not connect to: {provider_url}")
                self.w3 = None
        except ImportError:
            logger.warning("web3 not installed. Oracle runs in LOCAL mode only.")
        except Exception as e:
            logger.error(f"Web3 init failed: {e}")

    # ─── Core Pipeline ─────────────────────────────────────────────────

    async def evaluate_event(self, event: SeverityEvent, db: Any = None) -> Dict[str, Any]:
        """
        Evaluates a climate severity event and decides whether to trigger payout.

        Pipeline:
        1. Validate severity score
        2. Cross-check with historical baseline (optional)
        3. If severity >= threshold → trigger settlement
        4. Log to audit trail
        """
        import uuid
        from models.sqlalchemy_models import OracleEvent, BlockchainTransaction
        
        logger.info(
            f"Oracle evaluating event: token={event.token_id} "
            f"severity={event.severity_score} at ({event.latitude:.4f}, {event.longitude:.4f})"
        )

        event_uuid = f"evt_or_{uuid.uuid4().hex[:12]}"

        result = {
            "token_id": event.token_id,
            "severity_score": event.severity_score,
            "timestamp": event.timestamp.isoformat(),
            "location": {"lat": event.latitude, "lon": event.longitude},
            "oracle_mode": self.mode,
            "threshold": self.SEVERITY_THRESHOLD,
        }

        # Decision gate
        if event.severity_score >= self.SEVERITY_THRESHOLD:
            result["decision"] = "TRIGGER_PAYOUT"
            result["payout_percentage"] = self._calculate_payout_percentage(event.severity_score)

            if self.mode == "LOCAL":
                result["execution"] = "simulated"
                result["tx_hash"] = f"0x_mock_{event.token_id}_{int(event.timestamp.timestamp())}"
            elif self.w3 and self.contract_address:
                tx_result = await self._execute_payout(event)
                result.update(tx_result)
            else:
                result["execution"] = "deferred"
                result["reason"] = "No blockchain connection configured"

            self.pending_events.append(event)
        else:
            result["decision"] = "NO_ACTION"
            result["reason"] = f"Severity {event.severity_score} < threshold {self.SEVERITY_THRESHOLD}"

        if db:
            db_event = OracleEvent(
                event_id=event_uuid,
                token_id=str(event.token_id),
                latitude=event.latitude,
                longitude=event.longitude,
                disaster_type=event.source,
                severity_score=event.severity_score,
                ndvi=event.ndvi,
                soil_moisture=event.soil_moisture,
                payout_triggered=(result.get("decision") == "TRIGGER_PAYOUT"),
                payout_percentage=result.get("payout_percentage", 0.0),
                blockchain_tx_id=result.get("tx_hash"),
                status="TRIGGERED" if result.get("decision") == "TRIGGER_PAYOUT" else "EVALUATED"
            )
            db.add(db_event)
            
            if result.get("tx_hash") and result.get("decision") == "TRIGGER_PAYOUT":
                db_tx = BlockchainTransaction(
                    tx_hash=result["tx_hash"],
                    token_uid=str(event.token_id),
                    from_address="oracle",
                    to_address="policy_holder",
                    amount=result.get("payout_bps", 0) / 10000.0,
                    status="PENDING" if result.get("execution") == "simulated" else "CONFIRMED"
                )
                db.add(db_tx)
                
            try:
                await db.commit()
            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to persist Oracle Event to DB: {e}")

        self.processed_events.append(result)
        return result

    async def evaluate_batch(self, events: List[SeverityEvent], db: Any = None) -> List[Dict[str, Any]]:
        """Evaluate multiple events (e.g. from a scheduled scan)."""
        results = []
        for event in events:
            r = await self.evaluate_event(event, db=db)
            results.append(r)
        return results

    # ─── Settlement Execution ──────────────────────────────────────────

    def _calculate_payout_percentage(self, severity: float) -> float:
        """
        Maps severity score (3–5) to payout percentage (25%–100%).
        Linear interpolation between threshold and max severity.
        """
        if severity >= 5.0:
            return 1.0  # 100% payout
        elif severity >= self.SEVERITY_THRESHOLD:
            return round(0.25 + 0.75 * (severity - self.SEVERITY_THRESHOLD) / (5.0 - self.SEVERITY_THRESHOLD), 4)
        return 0.0

    async def _execute_payout(self, event: SeverityEvent) -> Dict[str, Any]:
        """
        Sends a signed transaction to the ClimatePolicy contract's triggerPayout function.
        Uses KMS signer if available, otherwise falls back to raw key.
        """
        try:
            if not self.w3 or not self.contract_address:
                return {"execution": "failed", "error": "No web3 or contract configured"}

            # Build transaction
            payout_pct = self._calculate_payout_percentage(event.severity_score)

            # ABI snippet for triggerPayout(uint256 tokenId, uint256 payoutBps)
            # payoutBps = payout percentage in basis points (10000 = 100%)
            payout_bps = int(payout_pct * 10000)

            tx_data = {
                "to": self.contract_address,
                "data": self._encode_trigger_payout(event.token_id, payout_bps),
                "gas": 200_000,
                "gasPrice": self.w3.eth.gas_price,
                "nonce": 0,  # Will be filled by signer
                "chainId": self.w3.eth.chain_id
            }

            # Sign via KMS or local key
            if self.kms_signer:
                signed_tx = await self.kms_signer.sign_transaction(tx_data)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx)
            else:
                # Fallback: use env private key (dev only)
                pk = os.getenv("ORACLE_PRIVATE_KEY")
                if not pk:
                    return {"execution": "failed", "error": "No signer available"}

                account = self.w3.eth.account.from_key(pk)
                tx_data["nonce"] = self.w3.eth.get_transaction_count(account.address)
                tx_data["from"] = account.address
                signed = account.sign_transaction(tx_data)
                tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)

            return {
                "execution": "success",
                "tx_hash": tx_hash.hex(),
                "payout_bps": payout_bps,
                "chain_id": tx_data["chainId"]
            }

        except Exception as e:
            logger.error(f"Payout execution failed: {e}")
            return {"execution": "failed", "error": str(e)}

    def _encode_trigger_payout(self, token_id: int, payout_bps: int) -> str:
        """Encode the triggerPayout function call (keccak selector + args)."""
        # triggerPayout(uint256,uint256) selector
        selector = "0xb3d3c8f1"
        token_hex = hex(token_id)[2:].zfill(64)
        bps_hex = hex(payout_bps)[2:].zfill(64)
        return selector + token_hex + bps_hex

    # ─── Multi-Oracle Consensus (Phase 6) ──────────────────────────────

    async def submit_vote(self, event: SeverityEvent, oracle_id: str) -> Dict[str, Any]:
        """
        For multi-oracle consensus: each oracle instance submits a vote.
        Payout only triggers when consensus_required votes are reached.
        """
        event.consensus_votes += 1
        logger.info(
            f"Oracle {oracle_id} voted on token {event.token_id}. "
            f"Votes: {event.consensus_votes}/{event.consensus_required}"
        )

        if event.consensus_votes >= event.consensus_required:
            return await self.evaluate_event(event)
        else:
            return {
                "token_id": event.token_id,
                "decision": "AWAITING_CONSENSUS",
                "votes": event.consensus_votes,
                "required": event.consensus_required
            }

    # ─── Status & Monitoring ───────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Returns oracle operational status."""
        return {
            "mode": self.mode,
            "blockchain_connected": self.w3 is not None and self.w3.is_connected() if self.w3 else False,
            "contract_address": self.contract_address,
            "kms_signer": self.kms_signer is not None,
            "pending_events": len(self.pending_events),
            "processed_total": len(self.processed_events),
            "threshold": self.SEVERITY_THRESHOLD,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
