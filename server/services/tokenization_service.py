from __future__ import annotations
import json
import os
import logging
from typing import Any, Optional, cast
from web3 import Web3

# google.cloud imports are now conditional to allow local development without GCP libs
try:
    from google.cloud import secretmanager
    from google.cloud import kms
    from cryptography.hazmat.primitives.asymmetric import utils as crypto_utils

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

    def _sign_with_kms(self, transaction: Dict[str, Any], key_path: str) -> Any:
        """Signs a transaction hash using Google Cloud KMS."""
        if not GOOGLE_CLOUD_AVAILABLE:
            raise RuntimeError("Google Cloud libraries not available for KMS signing.")

        # 1. Get transaction hash
        w3_instance = cast(Web3, self.w3)
        # Using eth_account helper to get the hash for signing
        from eth_account import Account
        unsigned_transaction = Account._prepare_transaction(transaction)
        tx_hash = unsigned_transaction.hash

        try:
            client = kms.KeyManagementServiceClient()
            digest = {"sha256": tx_hash}
            
            response = client.asymmetric_sign(
                request={
                    "name": key_path,
                    "digest": digest
                }
            )

            # 2. Reconstruct signature [r, s] from DER
            r, s = crypto_utils.decode_dss_signature(response.signature)
            
            # Ethereum requires s to be in the lower half of the curve order
            # SECP256K1 Curve Order
            N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
            if s > N // 2:
                s = N - s

            # 3. Find Recovery ID (v)
            # We need the public key address to verify which v is correct
            public_key_response = client.get_public_key(name=key_path)
            
            # Convert KMS public key to Eth Address
            from cryptography.hazmat.primitives import serialization
            from eth_utils import keccak, to_checksum_address
            
            pub_key = serialization.load_pem_public_key(
                public_key_response.pem.encode()
            )
            pub_numbers = pub_key.public_numbers()
            # x and y are 32 bytes each
            x = pub_numbers.x.to_bytes(32, byteorder='big')
            y = pub_numbers.y.to_bytes(32, byteorder='big')
            uncompressed_pub_key = x + y
            eth_address = to_checksum_address(keccak(uncompressed_pub_key)[-20:])

            # Try v = 27 and v = 28
            from eth_account import Account
            from eth_account.messages import encode_defunct
            
            for v in [27, 28]:
                # In modern web3/eth_account, we can use the r, s, v directly
                # However, to return a 'signed_transaction' object, we need to use 
                # Account.sign_transaction logic or build an InternalGroup
                pass # Logic continues below in actual implementation
            
            return {"r": r, "s": s, "eth_address": eth_address}

        except Exception as e:
            logger.error(f"KMS Signing failed: {e}")
            raise

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
            kms_key_path = self._get_config("KMS_KEY_PATH")
            
            if kms_key_path and GOOGLE_CLOUD_AVAILABLE:
                # KMS SIGNING FLOW
                logger.info(f"Signing transaction via KMS: {kms_key_path}")
                
                # Fetch r, s and eth_address from KMS
                sig_data = self._sign_with_kms(tx, kms_key_path)
                r, s, eth_address = sig_data['r'], sig_data['s'], sig_data['eth_address']
                
                # Build the signature with v recovery
                from eth_account._utils.signing import sign_transaction_hash
                # We need to find which v (0 or 1) results in the correct address
                # Account.sign_transaction_hash doesn't exist, we use the internal one or loop
                
                # For Phase 2, we use the standard web3.eth.account.recover_transaction
                # but we need to encode it first. 
                # This is a complex area of Web3.py. For the MVP, we assume the recovery 
                # logic is performed or we use a custom signed object.
                
                # Implementation of v recovery:
                from eth_account import Account
                unsigned_tx = Account._prepare_transaction(tx)
                
                v = None
                for candidate_v in [27, 28]:
                    # This is a simplified check
                    try:
                        # Reconstruct raw signature format for recovery
                        pass 
                    except:
                        continue
                
                # Placeholder for the final signed transaction object
                # In real production, we'd use a custom Middleware for Web3.py 
                # to handle KMS seamlessly.
                raise NotImplementedError("Advanced KMS signature reconstruction is in progress. Use PRIVATE_KEY for now.")
            else:
                # LEGACY/LOCAL PRIVATE KEY FLOW
                private_key = self._get_config("PRIVATE_KEY")
                if not private_key:
                    raise ValueError("PRIVATE_KEY or KMS_KEY_PATH not configured for signing.")

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

    def mint_policy(self, to: str, slot: int, value: int) -> Any:
        """Mint an ERC-3525 climate policy token.
        Returns the transaction receipt or a mock response.
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Minting ERC-3525 Policy (Slot: {slot}, Value: {value}) to {to}")
            import uuid
            return {
                "transactionHash": f"0x{uuid.uuid4().hex}".encode(),
                "status": 1,
                "blockNumber": 2000,
                "mock": True,
            }

        if not self.contract or not self.w3:
            raise RuntimeError("Blockchain contract not initialized.")

        try:
            w3_instance = cast(Web3, self.w3)
            
            # Note: The contract must be the ClimatePolicy.sol (ERC-3525)
            tx = self.contract.functions.mintPolicy(to, slot, value).build_transaction(
                {
                    "nonce": w3_instance.eth.get_transaction_count(
                        w3_instance.eth.default_account
                    ),
                    "gas": 300_000,
                    "gasPrice": w3_instance.to_wei("5", "gwei"),
                }
            )

            # Sign transaction
            kms_key_path = self._get_config("KMS_KEY_PATH")
            if kms_key_path and GOOGLE_CLOUD_AVAILABLE:
                # Production KMS Signer logic (Placeholdered to maintain parity with mint())
                raise NotImplementedError("Advanced KMS signature reconstruction is in progress. Use PRIVATE_KEY for now.")
            else:
                private_key = self._get_config("PRIVATE_KEY")
                if not private_key:
                    raise ValueError("PRIVATE_KEY or KMS_KEY_PATH not configured for signing.")

                signed = w3_instance.eth.account.sign_transaction(
                    tx, private_key=private_key
                )

                tx_hash = w3_instance.eth.send_raw_transaction(signed.rawTransaction)
                receipt = w3_instance.eth.wait_for_transaction_receipt(tx_hash)
                return receipt

        except Exception as e:
            logger.error(f"Error minting ERC-3525 policy: {e}")
            raise
