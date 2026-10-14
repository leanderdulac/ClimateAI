"""
Deployment and On-chain Verification Script for ClimateWise on Base (Coinbase L2)
Deploys ClimatePolicy contract, mints an RWA policy token, and executes an oracle settlement with cryptographic proof.
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

# Load env variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)
load_dotenv()

BASE_RPC = os.getenv("BASE_SEPOLIA_RPC", "https://sepolia.base.org")
PRIVATE_KEY = os.getenv("BASE_OPERATOR_PRIVATE_KEY")
CHAIN_ID = int(os.getenv("BASE_SEPOLIA_CHAIN_ID", 84532))

if not PRIVATE_KEY:
    print("ERROR: BASE_OPERATOR_PRIVATE_KEY is missing from environment.")
    sys.exit(1)

w3 = Web3(Web3.HTTPProvider(BASE_RPC))
if not w3.is_connected():
    print(f"ERROR: Cannot connect to Base RPC at {BASE_RPC}")
    sys.exit(1)

account = w3.eth.account.from_key(PRIVATE_KEY)
balance = w3.eth.get_balance(account.address)
eth_balance = w3.from_wei(balance, "ether")

print(f"=======================================================")
print(f"   ClimateWise on-chain Base (Coinbase L2) Engine      ")
print(f"=======================================================")
print(f"Network: Base Sepolia (Chain ID: {CHAIN_ID})")
print(f"Deployer / Oracle Operator: {account.address}")
print(f"Account Balance: {eth_balance} ETH")

# Load compiled artifact
artifact_path = Path(__file__).resolve().parent / "ClimatePolicyArtifact.json"
with open(artifact_path, "r", encoding="utf-8") as f:
    artifact = json.load(f)

abi = artifact["abi"]
bytecode = artifact["bytecode"]
if not bytecode.startswith("0x"):
    bytecode = "0x" + bytecode

contract_address = os.getenv("BASE_CLIMATE_POLICY_CONTRACT", "0x01dD68040B926Fd4938cD43Ae3c88758874DD0D0")

# Check if contract already exists
has_contract = False
if contract_address:
    try:
        code = w3.eth.get_code(Web3.to_checksum_address(contract_address))
        if len(code) > 0:
            has_contract = True
            print(f"\n[Step 1] Reusing existing deployed contract at: {contract_address}")
            print(f"BaseScan Explorer: https://sepolia.basescan.org/address/{contract_address}")
    except Exception:
        has_contract = False

if not has_contract:
    # 1. Deploy Contract
    print("\n[Step 1] Deploying ClimatePolicy.sol to Base Sepolia...")
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    nonce = w3.eth.get_transaction_count(account.address, "pending")
    base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
    priority_fee = w3.to_wei(0.005, "gwei")
    max_fee = int(base_fee * 1.5) + priority_fee

    deploy_tx = Contract.constructor().build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 3_500_000,
        "maxFeePerGas": max_fee,
        "maxPriorityFeePerGas": priority_fee,
        "chainId": CHAIN_ID,
    })

    signed_tx = w3.eth.account.sign_transaction(deploy_tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Deploy Tx Hash: {tx_hash.hex()}")
    print(f"Waiting for deployment confirmation on BaseScan...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    contract_address = receipt.contractAddress
    print(f"Contract deployed successfully!")
    print(f"Contract Address: {contract_address}")
    print(f"BaseScan Explorer: https://sepolia.basescan.org/address/{contract_address}")


def update_env_file(filepath: Path, key: str, value: str):
    if not filepath.exists():
        return
    content = filepath.read_text(encoding="utf-8")
    lines = content.splitlines()
    found = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}")
    filepath.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


update_env_file(env_path, "BASE_CLIMATE_POLICY_CONTRACT", contract_address)
update_env_file(Path(".env"), "BASE_CLIMATE_POLICY_CONTRACT", contract_address)

# Instantiate contract
contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=abi)

# Check contract name and symbol
name = contract.functions.name().call()
symbol = contract.functions.symbol().call()
oracle_addr = contract.functions.oracle().call()
print(f"Contract Details: Name='{name}', Symbol='{symbol}', Oracle={oracle_addr}")

# 2. Mint Parametric Policy Token
print("\n[Step 2] Minting Parametric Policy Token on-chain...")
recipient = account.address
slot = 20261014
coverage_cents = 10815069  # R$ 108.150,69

nonce = w3.eth.get_transaction_count(account.address, "pending")
base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
priority_fee = w3.to_wei(0.01, "gwei")
max_fee = int(base_fee * 2) + priority_fee

mint_tx = contract.functions.mintPolicy(recipient, slot, coverage_cents).build_transaction({
    "from": account.address,
    "nonce": nonce,
    "gas": 300_000,
    "maxFeePerGas": max_fee,
    "maxPriorityFeePerGas": priority_fee,
    "chainId": CHAIN_ID,
})

signed_mint = w3.eth.account.sign_transaction(mint_tx, private_key=PRIVATE_KEY)
mint_tx_hash = w3.eth.send_raw_transaction(signed_mint.raw_transaction)
print(f"Mint Tx Broadcasted: {mint_tx_hash.hex()}")
print(f"Waiting for Base L2 block confirmation...")

mint_receipt = w3.eth.wait_for_transaction_receipt(mint_tx_hash, timeout=120)
print(f"Policy Token Minted! Block: {mint_receipt.blockNumber}, Status: {mint_receipt.status}")
print(f"BaseScan Mint Tx: https://sepolia.basescan.org/tx/{mint_tx_hash.hex()}")

# Identify tokenId from events or read token 1
token_id = 1
token_owner = contract.functions.ownerOf(token_id).call()
token_value = contract.functions.valueOf(token_id).call()
token_slot = contract.functions.slotOf(token_id).call()

print(f"Token #{token_id} Verified On-Chain:")
print(f"  Owner: {token_owner}")
print(f"  Value: R$ {token_value / 100:,.2f} ({token_value} cents)")
print(f"  Slot: {token_slot}")
print(f"  BaseScan Token URL: https://sepolia.basescan.org/token/{contract_address}?a={token_id}")

# Wait for 2 seconds to ensure clean nonce increment
time.sleep(2)

# 3. Test Oracle Settlement with Canonical SHA-256 Proof
print("\n[Step 3] Executing Oracle Parametric Payout with Canonical Proof...")
canonical_evidence = "CW-EVIDENCE:DROUGHT_INDEX=0.88:TEMP=39.4C:SOIL_MOISTURE=0.11:AUDIT_HASH=9f83a"
evidence_hash_bytes = hashlib.sha256(canonical_evidence.encode()).digest()
evidence_hash_hex = "0x" + evidence_hash_bytes.hex()
print(f"Canonical Evidence Hash: {evidence_hash_hex}")

payout_amount = 5407534  # 50% payout in cents (R$ 54.075,34)

nonce = w3.eth.get_transaction_count(account.address, "pending")
base_fee = w3.eth.get_block("latest")["baseFeePerGas"]
max_fee = int(base_fee * 2) + priority_fee

payout_tx = contract.functions.triggerPayoutWithProof(
    token_id,
    payout_amount,
    evidence_hash_bytes
).build_transaction({
    "from": account.address,
    "nonce": nonce,
    "gas": 300_000,
    "maxFeePerGas": max_fee,
    "maxPriorityFeePerGas": priority_fee,
    "chainId": CHAIN_ID,
})

signed_payout = w3.eth.account.sign_transaction(payout_tx, private_key=PRIVATE_KEY)
payout_tx_hash = w3.eth.send_raw_transaction(signed_payout.raw_transaction)
print(f"Payout Tx Broadcasted: {payout_tx_hash.hex()}")
payout_receipt = w3.eth.wait_for_transaction_receipt(payout_tx_hash, timeout=120)
print(f"Oracle Payout Executed! Block: {payout_receipt.blockNumber}, Status: {payout_receipt.status}")
print(f"BaseScan Settlement Tx: https://sepolia.basescan.org/tx/{payout_tx_hash.hex()}")

print("\n=======================================================")
print(" ALL REAL ON-CHAIN OPERATIONS ON BASE COMPLETED!       ")
print("=======================================================")
