"""
Hathor Blockchain Service

Core service for interacting with Hathor Network.
Handles wallet management, transactions, and token operations.

Note: Uses Hathor HTTP API directly for maximum compatibility.
For full wallet operations, use hathor-wallet-lib or @hathor/wallet-lib (Node.js).
"""

import logging
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

import requests

from blockchain.hathor.config import HathorConfig, get_hathor_config

logger = logging.getLogger(__name__)


@dataclass
class TransactionResult:
    """Result of a blockchain transaction"""
    success: bool
    tx_hash: str
    token_uid: str
    amount: int
    address: str
    timestamp: datetime
    fee: int
    message: str = ""
    explorer_url: str = ""


@dataclass
class TokenInfo:
    """Information about a Hathor token"""
    uid: str
    name: str
    symbol: str
    total_supply: int
    decimals: int
    creator: str
    mintable: bool
    meltable: bool


class HathorService:
    """
    Core service for Hathor Network operations.
    
    Note: This service uses Hathor HTTP API directly.
    For production use with real wallets, integrate with:
    - hathor-wallet-lib (Python, when available)
    - @hathor/wallet-lib (Node.js)
    - Hathor Headless Wallet (API)
    
    Features:
    - Token information queries
    - Transaction status queries
    - Balance queries (via API)
    - Mock token operations for development
    
    For real token operations, use Hathor Wallet UI or integrate wallet library.
    """
    
    def __init__(self, config: Optional[HathorConfig] = None):
        """
        Initialize Hathor Service
        
        Args:
            config: Hathor configuration (uses default if not provided)
        """
        self.config = config or get_hathor_config()
        self.session = requests.Session()
        self._wallet_address: Optional[str] = None
        self._initialized = False
        
        logger.info(f"HathorService initialized for {self.config.NETWORK}")
    
    def initialize(self, seed: Optional[str] = None, address: Optional[str] = None) -> str:
        """
        Initialize wallet connection
        
        Args:
            seed: Optional seed (not used in API-only mode)
            address: Wallet address to use
            
        Returns:
            Wallet address
        """
        try:
            if address:
                self._wallet_address = address
            else:
                # For development, use a placeholder address
                # In production, integrate with real wallet library
                self._wallet_address = address or "development_placeholder_address"
            
            self._initialized = True
            logger.info(f"Wallet initialized: {self._wallet_address[:20]}...")
            return self._wallet_address
            
        except Exception as e:
            logger.error(f"Failed to initialize wallet: {str(e)}")
            raise
    
    def get_balance(self, token_uid: str = "00") -> Dict[str, Any]:
        """
        Get wallet balance for a token
        
        Args:
            token_uid: Token UID (default: HTR)
            
        Returns:
            Balance information
        """
        if not self._initialized:
            raise RuntimeError("Wallet not initialized")
        
        try:
            balance = self.wallet.get_balance(token_uid=token_uid)
            return {
                "token_uid": token_uid,
                "available": balance["available"],
                "locked": balance["locked"],
                "total": balance["available"] + balance["locked"]
            }
        except Exception as e:
            logger.error(f"Failed to get balance: {str(e)}")
            raise
    
    def create_climate_token(
        self,
        name: str,
        symbol: str,
        amount: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TransactionResult:
        """
        Create a new climate index token
        
        Note: In development mode, creates a mock token.
        For production, integrate with Hathor Wallet Library or use Hathor Wallet UI.
        
        Args:
            name: Token name
            symbol: Token symbol
            amount: Total supply
            metadata: Optional metadata (IPFS hash, etc.)
            
        Returns:
            TransactionResult with token details
        """
        if not self._initialized:
            raise RuntimeError("Wallet not initialized")
        
        try:
            # Generate mock token UID (in production, use real API)
            token_data = f"{name}{symbol}{amount}{datetime.now().isoformat()}"
            token_uid = hashlib.sha256(token_data.encode()).hexdigest()[:16]
            tx_hash = token_uid
            
            # In production, make API call to Hathor:
            # response = self.session.post(
            #     f"{self.config.rpc_url}/wallet/create-token",
            #     json={"name": name, "symbol": symbol, "amount": amount}
            # )
            # token_uid = response.json()["token"]
            
            # Store metadata if provided
            if metadata:
                self._store_token_metadata(token_uid, metadata)
            
            result = TransactionResult(
                success=True,
                tx_hash=tx_hash,
                token_uid=token_uid,
                amount=amount,
                address=self._wallet_address,
                timestamp=datetime.now(),
                fee=self.config.TOKEN_CREATION_FEE,
                message=f"Token {symbol} created successfully (development mode)",
                explorer_url=self.config.get_explorer_token_url(token_uid),
            )
            
            logger.info(f"Climate token created: {symbol} ({token_uid})")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create token: {str(e)}")
            raise
    
    def transfer_tokens(
        self,
        token_uid: str,
        amount: int,
        destination_address: str,
        message: str = "",
    ) -> TransactionResult:
        """
        Transfer tokens to another address
        
        Note: Development mode - mock implementation.
        
        Args:
            token_uid: Token to transfer
            amount: Amount to transfer (in smallest unit)
            destination_address: Recipient address
            message: Optional memo/message
            
        Returns:
            TransactionResult with transfer details
        """
        if not self._initialized:
            raise RuntimeError("Wallet not initialized")
        
        try:
            # Generate mock tx hash
            tx_data = f"{token_uid}{amount}{destination_address}{datetime.now().isoformat()}"
            tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()[:16]
            
            # In production:
            # response = self.session.post(
            #     f"{self.config.rpc_url}/wallet/send-tokens",
            #     json={"address": destination_address, "amount": amount, "token": token_uid}
            # )
            # tx_hash = response.json()["hash"]
            
            result = TransactionResult(
                success=True,
                tx_hash=tx_hash,
                token_uid=token_uid,
                amount=amount,
                address=destination_address,
                timestamp=datetime.now(),
                fee=1,  # Mock fee
                message=message or f"Transferred {amount} tokens",
                explorer_url=self.config.get_explorer_tx_url(tx_hash),
            )
            
            logger.info(f"Tokens transferred: {amount} {token_uid} -> {destination_address[:20]}...")
            return result
            
        except Exception as e:
            logger.error(f"Failed to transfer tokens: {str(e)}")
            raise
    
    def mint_tokens(
        self,
        token_uid: str,
        amount: int,
        mint_authority: str,
    ) -> TransactionResult:
        """
        Mint new tokens (if token is mintable)
        
        Args:
            token_uid: Token to mint
            amount: Amount to mint
            mint_authority: Mint authority address
            
        Returns:
            TransactionResult with mint details
        """
        if not self._initialized:
            raise RuntimeError("Wallet not initialized")
        
        try:
            # Create mint transaction
            tx = self.wallet.mint_tokens(
                token_uid=token_uid,
                amount=amount,
                mint_authority=mint_authority,
            )
            
            tx_hash = tx.get_tx_hash()
            
            result = TransactionResult(
                success=True,
                tx_hash=tx_hash,
                token_uid=token_uid,
                amount=amount,
                address=self.wallet.get_address(),
                timestamp=datetime.now(),
                fee=tx.get_fee(),
                message=f"Minted {amount} new tokens",
                explorer_url=self.config.get_explorer_tx_url(tx_hash),
            )
            
            logger.info(f"Tokens minted: {amount} {token_uid}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to mint tokens: {str(e)}")
            raise
    
    def melt_tokens(
        self,
        token_uid: str,
        amount: int,
        melt_authority: str,
    ) -> TransactionResult:
        """
        Melt (burn) tokens
        
        Args:
            token_uid: Token to melt
            amount: Amount to melt
            melt_authority: Melt authority address
            
        Returns:
            TransactionResult with melt details
        """
        if not self._initialized:
            raise RuntimeError("Wallet not initialized")
        
        try:
            # Create melt transaction
            tx = self.wallet.melt_tokens(
                token_uid=token_uid,
                amount=amount,
                melt_authority=melt_authority,
            )
            
            tx_hash = tx.get_tx_hash()
            
            result = TransactionResult(
                success=True,
                tx_hash=tx_hash,
                token_uid=token_uid,
                amount=amount,
                address=self.wallet.get_address(),
                timestamp=datetime.now(),
                fee=tx.get_fee(),
                message=f"Melted {amount} tokens",
                explorer_url=self.config.get_explorer_tx_url(tx_hash),
            )
            
            logger.info(f"Tokens melted: {amount} {token_uid}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to melt tokens: {str(e)}")
            raise
    
    def create_nano_contract(
        self,
        contract_type: str,
        conditions: Dict[str, Any],
        oracle_address: Optional[str] = None,
    ) -> TransactionResult:
        """
        Create a Nano Contract for climate index payouts
        
        Note: Development mode - mock implementation.
        For production, integrate with Hathor Nano Contract library.
        
        Args:
            contract_type: Type of contract (payout, multisig, timelock, etc.)
            conditions: Contract conditions
            oracle_address: Oracle address for data verification
            
        Returns:
            TransactionResult with contract details
        """
        if not self._initialized:
            raise RuntimeError("Wallet not initialized")
        
        try:
            # Generate mock tx hash for nano contract
            nc_data = f"{contract_type}{str(conditions)}{datetime.now().isoformat()}"
            tx_hash = hashlib.sha256(nc_data.encode()).hexdigest()[:16]
            
            # In production, create and deploy actual Nano Contract:
            # nc = NanoContract(wallet=self.wallet, script=script)
            # tx = nc.deploy()
            
            result = TransactionResult(
                success=True,
                tx_hash=tx_hash,
                token_uid="00",  # HTR
                amount=0,
                address=self._wallet_address,
                timestamp=datetime.now(),
                fee=1,  # Mock fee
                message=f"Nano Contract {contract_type} deployed (development mode)",
                explorer_url=self.config.get_explorer_tx_url(tx_hash),
            )
            
            logger.info(f"Nano Contract deployed: {contract_type} ({tx_hash[:20]}...)")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create nano contract: {str(e)}")
            raise
    
    def execute_nano_contract(
        self,
        contract_tx_hash: str,
        input_data: Dict[str, Any],
    ) -> TransactionResult:
        """
        Execute a Nano Contract (e.g., trigger payout)
        
        Note: Development mode - mock implementation.
        
        Args:
            contract_tx_hash: Hash of the deployed contract
            input_data: Data to satisfy contract conditions
            
        Returns:
            TransactionResult with execution details
        """
        if not self._initialized:
            raise RuntimeError("Wallet not initialized")
        
        try:
            # Generate mock tx hash
            tx_data = f"{contract_tx_hash}{str(input_data)}{datetime.now().isoformat()}"
            tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()[:16]
            
            # In production, load and execute actual Nano Contract:
            # nc = NanoContract.load(self.wallet, contract_tx_hash)
            # tx = nc.execute(input_data)
            
            result = TransactionResult(
                success=True,
                tx_hash=tx_hash,
                token_uid="00",
                amount=0,
                address=self._wallet_address,
                timestamp=datetime.now(),
                fee=1,  # Mock fee
                message="Nano Contract executed successfully (development mode)",
                explorer_url=self.config.get_explorer_tx_url(tx_hash),
            )
            
            logger.info(f"Nano Contract executed: {contract_tx_hash[:20]}...")
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute nano contract: {str(e)}")
            raise
    
    def get_token_info(self, token_uid: str) -> TokenInfo:
        """
        Get token information from blockchain
        
        Args:
            token_uid: Token UID to query
            
        Returns:
            TokenInfo with token details
        """
        try:
            # Query Hathor API
            url = f"{self.config.rpc_url}/token/{token_uid}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            return TokenInfo(
                uid=data["uid"],
                name=data["name"],
                symbol=data["symbol"],
                total_supply=data["total_supply"],
                decimals=data["decimals"],
                creator=data["creator"],
                mintable=data["mintable"],
                meltable=data["meltable"],
            )
            
        except Exception as e:
            logger.error(f"Failed to get token info: {str(e)}")
            raise
    
    def _store_token_metadata(
        self,
        token_uid: str,
        metadata: Dict[str, Any],
    ) -> str:
        """
        Store token metadata (e.g., on IPFS)
        
        Args:
            token_uid: Token to associate metadata with
            metadata: Metadata dictionary
            
        Returns:
            IPFS hash or storage reference
        """
        # For now, just log metadata
        # In production, store on IPFS and return hash
        metadata_with_timestamp = {
            **metadata,
            "stored_at": datetime.now().isoformat(),
            "token_uid": token_uid,
        }
        
        logger.info(f"Token metadata stored: {json.dumps(metadata_with_timestamp)}")
        return "ipfs_hash_placeholder"
    
    def get_wallet_address(self) -> str:
        """Get current wallet address"""
        if not self._initialized:
            raise RuntimeError("Wallet not initialized")
        return self.wallet.get_address()
    
    def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction status
        
        Args:
            tx_hash: Transaction hash to query
            
        Returns:
            Transaction status information
        """
        try:
            url = f"{self.config.rpc_url}/transaction/{tx_hash}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            return {
                "tx_hash": tx_hash,
                "confirmed": data.get("confirmed", False),
                "confirmations": data.get("confirmations", 0),
                "timestamp": data.get("timestamp"),
                "success": data.get("success", False),
            }
            
        except Exception as e:
            logger.error(f"Failed to get transaction status: {str(e)}")
            return {
                "tx_hash": tx_hash,
                "confirmed": False,
                "confirmations": 0,
                "error": str(e),
            }


# Singleton instance
hathor_service = HathorService()


def get_hathor_service() -> HathorService:
    """Get Hathor service instance"""
    return hathor_service
