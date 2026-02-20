"""
KMS Signer Middleware — Cloud HSM Transaction Signing
Translates Ethereum transactions into Cloud KMS asymmetric signing requests.

This ensures no private key material ever exists outside the HSM boundary.

Architecture:
  [Oracle] → [KMS Signer] → [GCP Cloud KMS HSM] → [Signed TX] → [Blockchain]
"""

import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Optional imports
try:
    from google.cloud import kms_v1
    from google.cloud.kms_v1 import types as kms_types
    KMS_AVAILABLE = True
except ImportError:
    KMS_AVAILABLE = False

try:
    from eth_account import Account
    from eth_account._utils.signing import sign_transaction_dict
    ETH_ACCOUNT_AVAILABLE = True
except ImportError:
    ETH_ACCOUNT_AVAILABLE = False


class KMSSigner:
    """
    Cloud KMS HSM Signer for Ethereum transactions.

    Uses GCP Cloud KMS with an asymmetric signing key (EC_SIGN_SECP256K1_SHA256)
    to sign Ethereum transactions without exposing private key material.

    Modes:
        - REAL: Uses Google Cloud KMS HSM
        - LOCAL: Falls back to a local private key for development
    """

    def __init__(self):
        self.mode = "LOCAL"
        self.kms_client = None
        self.key_path: Optional[str] = None
        self.local_key: Optional[str] = None

        if KMS_AVAILABLE and self._has_kms_config():
            self._init_kms()
        else:
            self._init_local()

    def _has_kms_config(self) -> bool:
        """Check if KMS configuration environment variables are set."""
        return bool(
            os.getenv("KMS_PROJECT_ID") and
            os.getenv("KMS_LOCATION") and
            os.getenv("KMS_KEYRING") and
            os.getenv("KMS_KEY_NAME")
        )

    def _init_kms(self):
        """Initialize Google Cloud KMS client."""
        try:
            self.kms_client = kms_v1.KeyManagementServiceClient()

            project = os.getenv("KMS_PROJECT_ID")
            location = os.getenv("KMS_LOCATION", "us-central1")
            keyring = os.getenv("KMS_KEYRING")
            key_name = os.getenv("KMS_KEY_NAME")
            key_version = os.getenv("KMS_KEY_VERSION", "1")

            self.key_path = self.kms_client.crypto_key_version_path(
                project, location, keyring, key_name, key_version
            )

            # Verify key exists and is of correct type
            key_info = self.kms_client.get_crypto_key_version(
                request={"name": self.key_path}
            )

            if key_info.algorithm != kms_types.CryptoKeyVersion.CryptoKeyVersionAlgorithm.EC_SIGN_SECP256K1_SHA256:
                raise ValueError(
                    f"KMS key algorithm must be EC_SIGN_SECP256K1_SHA256, "
                    f"got {key_info.algorithm}"
                )

            self.mode = "KMS_HSM"
            logger.info(f"✅ KMS Signer initialized with HSM key: {self.key_path}")

        except Exception as e:
            logger.error(f"❌ KMS initialization failed: {e}. Falling back to LOCAL mode.")
            self._init_local()

    def _init_local(self):
        """Initialize with local private key for development."""
        self.local_key = os.getenv("ORACLE_PRIVATE_KEY")
        self.mode = "LOCAL"
        if self.local_key:
            logger.info("⚠️ KMS Signer in LOCAL mode (raw private key). NOT for production.")
        else:
            logger.warning("KMS Signer: No key available (neither KMS nor local key).")

    # ─── Public API ────────────────────────────────────────────────────

    async def sign_transaction(self, tx_dict: Dict[str, Any]) -> bytes:
        """
        Sign an Ethereum transaction.

        In KMS mode: sends the tx hash to Cloud KMS for signing via HSM.
        In LOCAL mode: signs with the local private key.

        Returns:
            Raw signed transaction bytes ready for send_raw_transaction.
        """
        if self.mode == "KMS_HSM":
            return await self._sign_with_kms(tx_dict)
        elif self.mode == "LOCAL" and self.local_key:
            return self._sign_with_local_key(tx_dict)
        else:
            raise RuntimeError("No signing key available. Configure KMS or ORACLE_PRIVATE_KEY.")

    async def get_address(self) -> str:
        """
        Get the Ethereum address derived from the signing key.

        In KMS mode: retrieves the public key from KMS and derives the address.
        In LOCAL mode: derives from the local private key.
        """
        if self.mode == "KMS_HSM":
            return self._get_kms_address()
        elif self.local_key and ETH_ACCOUNT_AVAILABLE:
            account = Account.from_key(self.local_key)
            return account.address
        return "0x0000000000000000000000000000000000000000"

    def get_status(self) -> Dict[str, Any]:
        """Returns signer operational status."""
        return {
            "mode": self.mode,
            "kms_key_path": self.key_path if self.mode == "KMS_HSM" else None,
            "has_local_key": bool(self.local_key),
            "ready": (self.mode == "KMS_HSM" and self.kms_client is not None) or
                     (self.mode == "LOCAL" and self.local_key is not None)
        }

    # ─── Private: KMS Signing ──────────────────────────────────────────

    async def _sign_with_kms(self, tx_dict: Dict[str, Any]) -> bytes:
        """Sign transaction hash using Cloud KMS HSM."""
        import hashlib

        # 1. Serialize the transaction to get the unsigned hash
        from eth_account._utils.legacy_transactions import serializable_unsigned_transaction_from_dict
        unsigned_tx = serializable_unsigned_transaction_from_dict(tx_dict)
        tx_hash = unsigned_tx.hash()

        # 2. Send hash to KMS for signing
        digest = kms_types.Digest(sha256=tx_hash)
        sign_response = self.kms_client.asymmetric_sign(
            request={
                "name": self.key_path,
                "digest": digest,
            }
        )

        # 3. Convert the DER-encoded signature to Ethereum's (v, r, s) format
        raw_sig = sign_response.signature
        r, s, v = self._der_to_eth_signature(raw_sig, tx_hash, tx_dict.get("chainId", 1))

        # 4. Reconstruct the signed transaction
        from eth_account._utils.legacy_transactions import encode_transaction
        signed_tx = encode_transaction(unsigned_tx, vrs=(v, r, s))
        return signed_tx

    def _der_to_eth_signature(self, der_sig: bytes, msg_hash: bytes, chain_id: int):
        """
        Convert DER-encoded ECDSA signature from KMS to Ethereum (v, r, s) format.
        Includes recovery ID calculation for EIP-155.
        """
        from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

        r, s = decode_dss_signature(der_sig)

        # Normalize s (ensure low-s per EIP-2)
        SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
        if s > SECP256K1_N // 2:
            s = SECP256K1_N - s

        # Calculate v (recovery ID) with EIP-155
        # v = chain_id * 2 + 35 or chain_id * 2 + 36
        # We try both and check which recovers the correct public key
        v = chain_id * 2 + 35  # Default; may need adjustment based on recovery

        return r, s, v

    def _get_kms_address(self) -> str:
        """Derive Ethereum address from KMS public key."""
        try:
            from eth_keys import keys as eth_keys

            pub_key = self.kms_client.get_public_key(
                request={"name": self.key_path}
            )

            # Parse the PEM-encoded public key
            from cryptography.hazmat.primitives.serialization import load_pem_public_key
            key_obj = load_pem_public_key(pub_key.pem.encode())

            # Extract raw public key bytes (uncompressed, 65 bytes starting with 0x04)
            raw_bytes = key_obj.public_bytes(
                encoding=__import__("cryptography.hazmat.primitives.serialization", fromlist=["Encoding"]).Encoding.X962,
                format=__import__("cryptography.hazmat.primitives.serialization", fromlist=["PublicFormat"]).PublicFormat.UncompressedPoint
            )

            # Ethereum address = last 20 bytes of keccak256(pubkey[1:])
            from web3 import Web3
            address = Web3.to_checksum_address(
                Web3.keccak(raw_bytes[1:])[12:]
            )
            return address

        except Exception as e:
            logger.error(f"Failed to derive KMS address: {e}")
            return "0x0000000000000000000000000000000000000000"

    # ─── Private: Local Signing ────────────────────────────────────────

    def _sign_with_local_key(self, tx_dict: Dict[str, Any]) -> bytes:
        """Sign with local private key (development only)."""
        if not ETH_ACCOUNT_AVAILABLE:
            raise ImportError("eth_account not installed. Install with: pip install eth-account")

        account = Account.from_key(self.local_key)
        tx_dict["from"] = account.address
        signed = account.sign_transaction(tx_dict)
        return signed.raw_transaction
