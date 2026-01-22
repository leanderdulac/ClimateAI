from __future__ import annotations
import json
import os
import logging
from typing import Any, Optional, cast
from web3 import Web3

# google.cloud imports are now conditional to allow local development without GCP libs
try:
    from google.cloud import secretmanager

    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False

logger = logging.getLogger(__name__)


class TokenizationService:
    """Service responsible for interacting with the Google Cloud Blockchain node
    and minting ERC‑20 climate tokens.

    Supports fallback to environment variables and a mock mode for local development.
    """

    def __init__(self) -> None:
        self.w3: Optional[Web3] = None
        self.contract: Any = None
        self.mock_mode: bool = False
        self._initialize_service()

    def _initialize_service(self) -> None:
        """Initializes the Web3 connection and contract using Secrets or Env Vars."""

        # 1. Attempt to load configuration
        node_url = self._get_config("BC_NODE_URL")
        contract_address = self._get_config("CONTRACT_ADDRESS")
        abi_json = self._get_config("CONTRACT_ABI")

        # 2. Check if we have enough info to connect
        if not node_url:
            logger.warning("BC_NODE_URL not found. Switching to MOCK mode.")
            self.mock_mode = True
            return

        try:
            self.w3 = Web3(Web3.HTTPProvider(node_url))
            # Explicit check for w3 existence for mypy
            if self.w3 and not self.w3.is_connected():
                raise ConnectionError(
                    f"Could not connect to Blockchain Node at {node_url}"
                )

            logger.info(f"Connected to Blockchain Node: {node_url}")

            if contract_address and abi_json and self.w3:
                try:
                    contract_abi = json.loads(abi_json)
                    self.contract = self.w3.eth.contract(
                        address=contract_address, abi=contract_abi
                    )

                    # Set default account (dev mode only)
                    if self.w3.eth.accounts:
                        self.w3.eth.default_account = self.w3.eth.accounts[0]
                except json.JSONDecodeError:
                    logger.error("Invalid CONTRACT_ABI JSON format.")
            else:
                logger.warning(
                    "Contract address or ABI missing. Contract interaction disabled."
                )

        except Exception as e:
            logger.error(
                f"Failed to initialize Blockchain service: {e}. Switching to MOCK mode."
            )
            self.mock_mode = True
            self.w3 = None
            self.contract = None

    def _get_config(self, key: str) -> Optional[str]:
        """Retrieves config from Env Vars (priority) or Google Secret Manager."""
        # 1. Try Environment Variable first (Local Dev override)
        val = os.getenv(key)
        if val:
            return val

        # 2. Try Google Secret Manager if available
        if GOOGLE_CLOUD_AVAILABLE:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            if project_id:
                try:
                    client = secretmanager.SecretManagerServiceClient()
                    secret_name = f"projects/{project_id}/secrets/{key}/versions/latest"
                    response = client.access_secret_version(name=secret_name)
                    return response.payload.data.decode("UTF-8")
                except Exception as e:
                    logger.debug(f"Secret Manager lookup failed for {key}: {e}")

        return None

    def mint(self, to: str, amount: int) -> Any:
        """Mint `amount` tokens to address `to`.
        Returns the transaction receipt or a mock response.
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Minting {amount} tokens to {to}")
            return {
                "transactionHash": b"mock_tx_hash_0x123",
                "status": 1,
                "blockNumber": 1000,
                "mock": True,
            }

        if not self.contract or not self.w3:
            raise RuntimeError("Blockchain contract not initialized.")

        try:
            # Build transaction
            # Using cast or asserting self.w3 is not None (already checked above)
            w3_instance = cast(Web3, self.w3)

            tx = self.contract.functions.mint(to, amount).buildTransaction(
                {
                    "nonce": w3_instance.eth.get_transaction_count(
                        w3_instance.eth.default_account
                    ),
                    "gas": 200_000,
                    "gasPrice": w3_instance.to_wei("5", "gwei"),
                }
            )

            # Sign transaction
            # WARNING: In production, use a secure signer (e.g., Google Cloud KMS)
            private_key = self._get_config("PRIVATE_KEY")
            if not private_key:
                raise ValueError("PRIVATE_KEY not configured for signing transactions.")

            signed = w3_instance.eth.account.sign_transaction(
                tx, private_key=private_key
            )

            # Send and wait
            tx_hash = w3_instance.eth.send_raw_transaction(signed.rawTransaction)
            receipt = w3_instance.eth.wait_for_transaction_receipt(tx_hash)
            return receipt

        except Exception as e:
            logger.error(f"Error minting tokens: {e}")
            raise
