"""
Hathor Blockchain Configuration

Configuration settings for Hathor Network integration.
Supports both testnet (Mumbai) and mainnet.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class HathorConfig(BaseSettings):
    """Hathor Network Configuration"""
    
    # Network Settings
    NETWORK: str = Field(default="testnet", description="Network: testnet or mainnet")
    
    # RPC Endpoints
    HATHOR_TESTNET_RPC: str = Field(
        default="https://node.testnet.hathor.network",
        description="Hathor Testnet RPC URL"
    )
    HATHOR_MAINNET_RPC: str = Field(
        default="https://node.hathor.network",
        description="Hathor Mainnet RPC URL"
    )
    
    # Explorer URLs
    HATHOR_TESTNET_EXPLORER: str = Field(
        default="https://explorer.testnet.hathor.network",
        description="Hathor Testnet Explorer URL"
    )
    HATHOR_MAINNET_EXPLORER: str = Field(
        default="https://explorer.hathor.network",
        description="Hathor Mainnet Explorer URL"
    )
    
    # Wallet Configuration
    HATHOR_WALLET_SEED: str = Field(
        default="",
        description="Hathor wallet seed (24 words)"
    )
    HATHOR_WALLET_ADDRESS: str = Field(
        default="",
        description="Hathor wallet address"
    )
    
    # Token Configuration
    CLIMATE_TOKEN_SYMBOL: str = Field(
        default="CLMT",
        description="Climate Token Symbol"
    )
    CLIMATE_TOKEN_NAME: str = Field(
        default="Climate Index Token",
        description="Climate Token Name"
    )
    CLIMATE_TOKEN_INITIAL_SUPPLY: int = Field(
        default=1_000_000,
        description="Initial token supply"
    )
    
    # Transaction Configuration
    DEFAULT_FEE_PER_BYTE: int = Field(
        default=1,
        description="Default fee per byte in HTR"
    )
    TOKEN_CREATION_FEE: int = Field(
        default=100,  # 1 HTR
        description="Fee for token creation in HTR"
    )
    
    # Oracle Configuration
    ORACLE_ADDRESS: Optional[str] = Field(
        default=None,
        description="Oracle wallet address for nano contracts"
    )
    
    @property
    def rpc_url(self) -> str:
        """Get RPC URL based on network"""
        if self.NETWORK == "mainnet":
            return self.HATHOR_MAINNET_RPC
        return self.HATHOR_TESTNET_RPC
    
    @property
    def explorer_url(self) -> str:
        """Get explorer URL based on network"""
        if self.NETWORK == "mainnet":
            return self.HATHOR_MAINNET_EXPLORER
        return self.HATHOR_TESTNET_EXPLORER
    
    @property
    def is_testnet(self) -> bool:
        """Check if using testnet"""
        return self.NETWORK == "testnet"
    
    def get_explorer_tx_url(self, tx_hash: str) -> str:
        """Get explorer URL for transaction"""
        return f"{self.explorer_url}/transaction/{tx_hash}"
    
    def get_explorer_address_url(self, address: str) -> str:
        """Get explorer URL for address"""
        return f"{self.explorer_url}/address/{address}"
    
    def get_explorer_token_url(self, token_uid: str) -> str:
        """Get explorer URL for token"""
        return f"{self.explorer_url}/token_detail/{token_uid}"
    
    class Config:
        env_file = ".env"
        env_prefix = "HATHOR_"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# Global configuration instance
hathor_config = HathorConfig()


def get_hathor_config() -> HathorConfig:
    """Get Hathor configuration instance"""
    return hathor_config
