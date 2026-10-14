"""
Base Blockchain Configuration (Coinbase Ethereum L2)
Settings for Base Sepolia Testnet and Base Mainnet.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    """Configuration for Base Network (Coinbase L2)."""

    # Network Selection: "sepolia" or "mainnet"
    NETWORK: str = Field(default="sepolia", description="Base network: 'sepolia' or 'mainnet'")

    # RPC Endpoints (Official public endpoints)
    BASE_SEPOLIA_RPC: str = Field(
        default="https://sepolia.base.org",
        description="Base Sepolia testnet RPC URL",
    )
    BASE_MAINNET_RPC: str = Field(
        default="https://mainnet.base.org",
        description="Base Mainnet RPC URL",
    )

    # Chain IDs
    BASE_SEPOLIA_CHAIN_ID: int = Field(default=84532, description="Base Sepolia Chain ID")
    BASE_MAINNET_CHAIN_ID: int = Field(default=8453, description="Base Mainnet Chain ID")

    # Explorers (BaseScan)
    BASE_SEPOLIA_EXPLORER: str = Field(
        default="https://sepolia.basescan.org",
        description="Base Sepolia block explorer URL",
    )
    BASE_MAINNET_EXPLORER: str = Field(
        default="https://basescan.org",
        description="Base Mainnet block explorer URL",
    )

    # Smart Contract Deployments
    BASE_CLIMATE_POLICY_CONTRACT: Optional[str] = Field(
        default=None,
        description="Deployed ClimatePolicy ERC-3525 contract address on Base",
    )

    # Native USDC on Base (Circle Official)
    BASE_SEPOLIA_USDC: str = Field(
        default="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        description="Circle USDC on Base Sepolia",
    )
    BASE_MAINNET_USDC: str = Field(
        default="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        description="Circle Native USDC on Base Mainnet",
    )

    # Operator / Relayer Configuration
    BASE_OPERATOR_PRIVATE_KEY: Optional[str] = Field(
        default=None,
        description="Operator/Oracle private key for signing transactions (optional if KMS used)",
    )
    BASE_GAS_LIMIT_DEFAULT: int = Field(default=250_000, description="Default gas limit for policy operations")

    @property
    def rpc_url(self) -> str:
        """Returns the active RPC URL based on NETWORK."""
        return self.BASE_MAINNET_RPC if self.NETWORK == "mainnet" else self.BASE_SEPOLIA_RPC

    @property
    def chain_id(self) -> int:
        """Returns the active Chain ID."""
        return self.BASE_MAINNET_CHAIN_ID if self.NETWORK == "mainnet" else self.BASE_SEPOLIA_CHAIN_ID

    @property
    def explorer_url(self) -> str:
        """Returns the active Explorer URL."""
        return self.BASE_MAINNET_EXPLORER if self.NETWORK == "mainnet" else self.BASE_SEPOLIA_EXPLORER

    @property
    def usdc_address(self) -> str:
        """Returns the active USDC token address."""
        return self.BASE_MAINNET_USDC if self.NETWORK == "mainnet" else self.BASE_SEPOLIA_USDC

    @property
    def is_testnet(self) -> bool:
        return self.NETWORK != "mainnet"

    def get_explorer_tx_url(self, tx_hash: str) -> str:
        return f"{self.explorer_url}/tx/{tx_hash}"

    def get_explorer_address_url(self, address: str) -> str:
        return f"{self.explorer_url}/address/{address}"

    def get_explorer_token_url(self, contract_address: str, token_id: int) -> str:
        return f"{self.explorer_url}/token/{contract_address}?a={token_id}"

    class Config:
        env_prefix = ""
        extra = "ignore"


@lru_cache()
def get_base_config() -> BaseConfig:
    return BaseConfig()
