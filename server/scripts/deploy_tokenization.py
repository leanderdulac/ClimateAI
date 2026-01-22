#!/usr/bin/env python3
"""
Deploy Script for ClimateToken (ERC-20)
Usage: python3 deploy_tokenization.py

Env Vars required:
- BC_NODE_URL: RPC URL for the blockchain node (e.g., Sepolia)
- PRIVATE_KEY: Private key of the deployer account
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

from web3 import Web3
from solcx import compile_standard, install_solc

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
CONTRACT_REL_PATH = "../../contracts/Tokenization.sol"
SOLC_VERSION = "0.8.0"

def get_env_var(name: str, required: bool = True) -> str:
    val = os.getenv(name)
    if not val and required:
        logger.error(f"Missing required environment variable: {name}")
        sys.exit(1)
    return val or ""

def compile_contract(contract_path: Path) -> Dict[str, Any]:
    """Compiles the Solidity contract using solcx."""
    logger.info(f"Installing solc version {SOLC_VERSION}...")
    install_solc(SOLC_VERSION)

    with open(contract_path, "r") as f:
        source = f.read()

    logger.info("Compiling contract...")
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {contract_path.name: {"content": source}},
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                }
            },
        },
        solc_version=SOLC_VERSION,
    )
    return compiled_sol

def deploy():
    # 1. Setup
    node_url = get_env_var("BC_NODE_URL")
    private_key = get_env_var("PRIVATE_KEY")
    
    contract_path = Path(__file__).parent / CONTRACT_REL_PATH
    if not contract_path.exists():
        logger.error(f"Contract file not found at: {contract_path}")
        sys.exit(1)

    # 2. Connect to Blockchain
    w3 = Web3(Web3.HTTPProvider(node_url))
    if not w3.is_connected():
        logger.error(f"Failed to connect to node at {node_url}")
        sys.exit(1)
    
    account = w3.eth.account.from_key(private_key)
    logger.info(f"Deploying from account: {account.address}")
    logger.info(f"Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} ETH")

    # 3. Compile
    compiled = compile_contract(contract_path)
    
    # Extract Bytecode and ABI
    # Assumes contract name is 'ClimateToken' inside Tokenization.sol
    contract_data = compiled["contracts"][contract_path.name]["ClimateToken"]
    bytecode = contract_data["evm"]["bytecode"]["object"]
    abi = contract_data["abi"]

    # 4. Deploy
    logger.info("Building deployment transaction...")
    ClimateToken = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Construct constructor args (Name, Symbol)
    token_name = os.getenv("TOKEN_NAME", "ClimateAI Token")
    token_symbol = os.getenv("TOKEN_SYMBOL", "CLIM")

    tx = ClimateToken.constructor(token_name, token_symbol).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.eth.gas_price,
    })

    logger.info("Signing and sending transaction...")
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    logger.info(f"Transaction sent! Hash: {tx_hash.hex()}")
    logger.info("Waiting for receipt...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    # 5. Output Results
    contract_address = tx_receipt.contractAddress # type: ignore
    logger.info("✅ Deployment Successful!")
    logger.info("-" * 40)
    logger.info(f"Contract Address: {contract_address}")
    logger.info("-" * 40)
    
    # Save Artifacts
    output_data = {
        "address": contract_address,
        "abi": abi,
        "network": w3.eth.chain_id
    }
    
    output_file = Path("deployed_contract.json")
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Deployment artifacts saved to {output_file.absolute()}")
    logger.info("\nNEXT STEPS for Google Secret Manager / .env:")
    logger.info(f"CONTRACT_ADDRESS={contract_address}")
    logger.info(f"CONTRACT_ABI={json.dumps(json.dumps(abi))}") # Double encoded for JSON string inside string if needed

if __name__ == "__main__":
    deploy()
