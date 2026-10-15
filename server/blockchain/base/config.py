"""Base L2 (Coinbase) configuration. All fields optional so the app can boot unset."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def _env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


def _env_int(name: str) -> Optional[int]:
    raw = _env(name)
    if not raw:
        return None
    try:
        return int(raw, 0)
    except ValueError:
        return None


@dataclass(frozen=True)
class BaseL2Config:
    rpc_url: str
    chain_id: Optional[int]
    explorer_url: str
    contract_address: str
    operator_address: str

    @property
    def configured(self) -> bool:
        return bool(self.rpc_url)


def get_base_config() -> BaseL2Config:
    return BaseL2Config(
        rpc_url=_env("BASE_RPC_URL"),
        chain_id=_env_int("BASE_CHAIN_ID"),
        explorer_url=_env("BASE_EXPLORER_URL", "https://sepolia.basescan.org"),
        contract_address=(
            _env("BASE_CONTRACT_ADDRESS") or _env("CLIMATE_POLICY_CONTRACT")
        ),
        operator_address=_env("BASE_OPERATOR_ADDRESS"),
    )
