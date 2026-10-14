"""
Unit tests for the Enhanced Parametric Climate Oracle Service:
- Multi-Source Triangulation (2-of-3 Corroboration Rule)
- Canonical Deterministic Cryptographic Evidence Hashing (SHA-256 / IPFS CID)
- M-of-N Cryptographic Consensus Voting
- Audit Dossier Retrieval
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.oracle_service import (
    OracleService,
    SeverityEvent,
    SignedOracleVote,
    compute_evidence_hash,
    generate_ipfs_cid,
    canonical_json_dump,
)


@pytest.fixture
def oracle():
    return OracleService()


def test_canonical_json_and_evidence_hash():
    """Verify deterministic hashing regardless of key ordering."""
    payload_a = {"token_id": 101, "disaster": "flood", "severity": 4.5}
    payload_b = {"severity": 4.5, "token_id": 101, "disaster": "flood"}

    dump_a = canonical_json_dump(payload_a)
    dump_b = canonical_json_dump(payload_b)
    assert dump_a == dump_b

    hash_a = compute_evidence_hash(payload_a)
    hash_b = compute_evidence_hash(payload_b)
    assert hash_a.startswith("0x")
    assert len(hash_a) == 66  # 0x + 64 hex characters
    assert hash_a == hash_b

    cid = generate_ipfs_cid(hash_a)
    assert cid.startswith("bafybeicw")


def test_triangulation_single_source_failure(oracle):
    """Test 2-of-3 rule: Only 1 source breaches -> Quorum fails, NO payout."""
    dossier = oracle.build_triangulated_dossier(
        token_id=77,
        latitude=-23.55,
        longitude=-46.63,
        disaster_type="flood",
        satellite_data={"metric_value": 0.10, "threshold": 0.35},  # NOT breached
        ground_data={"metric_value": 150.0, "threshold": 100.0},    # BREACHED
        news_data={"metric_value": 1.5, "threshold": 3.0},          # NOT breached
    )

    assert dossier.token_id == 77
    assert dossier.corroborating_sources_count == 1
    assert dossier.total_sources_count == 3
    assert dossier.quorum_reached is False
    assert dossier.recommended_payout_pct == 0.0
    assert dossier.evidence_hash.startswith("0x")


def test_triangulation_two_sources_corroborate(oracle):
    """Test 2-of-3 rule: 2 sources breach -> Quorum reached, 75% payout."""
    dossier = oracle.build_triangulated_dossier(
        token_id=88,
        latitude=-23.55,
        longitude=-46.63,
        disaster_type="flood",
        satellite_data={"metric_value": 0.42, "threshold": 0.35},   # BREACHED (NDWI water index)
        ground_data={"metric_value": 125.0, "threshold": 100.0},   # BREACHED (Rainfall 125mm)
        news_data={"metric_value": 2.0, "threshold": 3.0},          # NOT breached
    )

    assert dossier.corroborating_sources_count == 2
    assert dossier.quorum_reached is True
    assert dossier.recommended_payout_pct == 0.75
    assert oracle.get_audit_dossier(dossier.evidence_hash) is not None
    assert oracle.get_audit_dossier(dossier.ipfs_cid) is not None


def test_triangulation_three_sources_unanimous(oracle):
    """Test 2-of-3 rule: 3 sources breach -> Unanimous 100% payout."""
    dossier = oracle.build_triangulated_dossier(
        token_id=99,
        latitude=-23.55,
        longitude=-46.63,
        disaster_type="flood",
        satellite_data={"metric_value": 0.55, "threshold": 0.35},   # BREACHED
        ground_data={"metric_value": 180.0, "threshold": 100.0},   # BREACHED
        news_data={"metric_value": 4.5, "threshold": 3.0},          # BREACHED
    )

    assert dossier.corroborating_sources_count == 3
    assert dossier.quorum_reached is True
    assert dossier.recommended_payout_pct == 1.0


@pytest.mark.asyncio
async def test_mofn_cryptographic_consensus_settlement(oracle):
    """Test M-of-N decentralized node voting leading to settlement."""
    evidence_hash = "0xabc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abc"
    token_id = 500

    # Vote 1 from Node 1 (Akash Europe)
    vote1 = SignedOracleVote(
        vote_id="vote-1",
        token_id=token_id,
        oracle_node_id="akash-node-eu-1",
        node_address="0x1111111111111111111111111111111111111111",
        evidence_hash=evidence_hash,
        decision="APPROVE_PAYOUT",
        payout_bps=10000,
        signature="0x_sig_node1_valid",
    )
    res1 = await oracle.submit_signed_vote(vote1)
    assert res1["status"] == "AWAITING_CONSENSUS"
    assert res1["current_votes"] == 1
    assert res1["required_quorum"] == 2

    # Vote 2 from Node 2 (Akash USA) -> Reaches Quorum (2 of 2)
    vote2 = SignedOracleVote(
        vote_id="vote-2",
        token_id=token_id,
        oracle_node_id="akash-node-us-1",
        node_address="0x2222222222222222222222222222222222222222",
        evidence_hash=evidence_hash,
        decision="APPROVE_PAYOUT",
        payout_bps=10000,
        signature="0x_sig_node2_valid",
    )
    res2 = await oracle.submit_signed_vote(vote2)
    assert res2["status"] == "QUORUM_REACHED_SETTLED"
    assert res2["votes_count"] == 2
    assert "payout_result" in res2
    assert res2["payout_result"]["decision"] == "TRIGGER_PAYOUT"


@pytest.mark.asyncio
async def test_backwards_compatible_evaluate_event(oracle):
    """Ensure standard evaluate_event continues to work seamlessly."""
    event = SeverityEvent(
        token_id=12,
        latitude=-23.55,
        longitude=-46.63,
        severity_score=4.0,
        ndvi=0.20,
        soil_moisture=0.15,
        source="vertex_ai",
    )
    res = await oracle.evaluate_event(event)
    assert res["decision"] == "TRIGGER_PAYOUT"
    assert res["payout_percentage"] > 0
    assert "evidence_hash" in res
    assert "ipfs_cid" in res
    assert res["evidence_hash"].startswith("0x")
