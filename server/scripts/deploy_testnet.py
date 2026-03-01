import os
import sys
import json
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

load_dotenv()

def deploy():
    # 1. Configuration
    rpc_url = os.getenv("BC_NODE_URL", "https://rpc-mumbai.maticvigil.com")
    private_key = os.getenv("PRIVATE_KEY")
    sender_address = os.getenv("SENDER_ADDRESS")
    usdc_address = os.getenv("USDC_ADDRESS", "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174") # Mock USDC

    if not private_key:
        print("Error: PRIVATE_KEY not found in .env")
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"Error: Could not connect to RPC at {rpc_url}")
        return

    print(f"Connected to Blockchain. Network ID: {w3.eth.chain_id}")

    # 2. Compile Contracts
    contracts_dir = os.path.join(os.path.dirname(__file__), "../../contracts")
    def compile_contract(filename, contract_name):
        with open(os.path.join(contracts_dir, filename), "r") as f:
            source = f.read()
        install_solc("0.8.0")
        compiled = compile_standard(
            {
                "language": "Solidity",
                "sources": {filename: {"content": source}},
                "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode.object"]}}}
            },
            solclc_version="0.8.0",
        )
        return compiled["contracts"][filename][contract_name]

    print("Compiling contracts...")
    policy_data = compile_contract("ClimatePolicy.sol", "ClimatePolicy")
    vault_data = compile_contract("RiskVault.sol", "RiskVault")

    def send_deploy_tx(abi, bytecode, args):
        Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
        nonce = w3.eth.get_transaction_count(sender_address)
        tx = Contract.constructor(*args).build_transaction({
            "chainId": w3.eth.chain_id, "gasPrice": w3.eth.gas_price,
            "from": sender_address, "nonce": nonce,
        })
        signed = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        return w3.eth.wait_for_transaction_receipt(tx_hash)

    # 3. Deploy Policy
    print("Deploying ClimatePolicy...")
    policy_receipt = send_deploy_tx(policy_data["abi"], policy_data["evm"]["bytecode"]["object"], ["ClimateWise Policy", "CPOL"])
    print(f"Policy deployed at: {policy_receipt.contractAddress}")

    # 4. Deploy Vault
    print("Deploying RiskVault...")
    vault_receipt = send_deploy_tx(
        vault_data["abi"], 
        vault_data["evm"]["bytecode"]["object"], 
        [usdc_address, "ClimateWise Risk Vault", "cRWA", policy_receipt.contractAddress]
    )
    print(f"Vault deployed at: {vault_receipt.contractAddress}")

    # 5. Save Artifacts for Backend
    artifacts = {
        "policy": {"address": policy_receipt.contractAddress, "abi": policy_data["abi"]},
        "vault": {"address": vault_receipt.contractAddress, "abi": vault_data["abi"]},
        "network": {"id": w3.eth.chain_id, "rpc": rpc_url}
    }
    with open("contract_artifacts_full.json", "w") as f:
        json.dump(artifacts, f, indent=2)
    print("Deployment complete. Artifacts saved to contract_artifacts_full.json")

if __name__ == "__main__":
    deploy()

if __name__ == "__main__":
    deploy()
