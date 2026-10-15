"""Probe Base L2 RPC without failing app startup when env is missing."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx

from blockchain.base.config import get_base_config

PROBE_TIMEOUT_SECONDS = 2.5


def _hex_int(value: Any) -> Optional[int]:
    if not isinstance(value, str):
        return None
    try:
        return int(value, 16)
    except ValueError:
        return None


async def _rpc(rpc_url: str, method: str) -> Any:
    async with httpx.AsyncClient(timeout=PROBE_TIMEOUT_SECONDS) as client:
        response = await client.post(
            rpc_url,
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": []},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise RuntimeError(str(payload["error"]))
        return payload.get("result")


async def probe_base_status() -> Dict[str, Any]:
    """Return Base L2 health. Never raises; never leaks RPC credentials."""
    checked = datetime.now(timezone.utc).isoformat()
    config = get_base_config()
    contracts = {
        "policy": config.contract_address or None,
        "operator": config.operator_address or None,
    }

    if not config.configured:
        return {
            "status": "not_configured",
            "network": "base",
            "chain_id": config.chain_id,
            "latest_block": None,
            "explorer_url": config.explorer_url or None,
            "contracts": contracts,
            "last_checked": checked,
        }

    try:
        chain_hex, block_hex = await _rpc(config.rpc_url, "eth_chainId"), await _rpc(
            config.rpc_url, "eth_blockNumber"
        )
        observed_chain = _hex_int(chain_hex)
        latest_block = _hex_int(block_hex)
        chain_mismatch = (
            config.chain_id is not None
            and observed_chain is not None
            and observed_chain != config.chain_id
        )
        return {
            "status": "offline" if chain_mismatch else "online",
            "network": "base",
            "chain_id": observed_chain if observed_chain is not None else config.chain_id,
            "latest_block": latest_block,
            "explorer_url": config.explorer_url or None,
            "contracts": contracts,
            "last_checked": checked,
        }
    except Exception:
        return {
            "status": "offline",
            "network": "base",
            "chain_id": config.chain_id,
            "latest_block": None,
            "explorer_url": config.explorer_url or None,
            "contracts": contracts,
            "last_checked": checked,
        }
