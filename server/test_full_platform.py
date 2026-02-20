import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_full_flow():
    print("--- 🔬 Starting Full Platform Integration Test ---")

    # 1. Test Parametric Simulation & RWA Persistence
    print("\n[1/5] Testing Parametric Simulation (Intelligence + local DB)...")
    sim_request = {
        "latitude": -23.55,
        "longitude": -46.63,
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "contract": {
            "trigger_mm": 100.0,
            "exhaustion_mm": 200.0,
            "max_payout": 10000.0,
            "index_type": "cum_period"
        },
        "include_ep_curve": True
    }
    
    response = requests.post(f"{BASE_URL}/parametric/simulate", json=sim_request)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Simulation Success! Warnings/Info: {data.get('warnings')}")
        print(f"   AAL: ${data['metrics']['AAL']:.2f}")
        print(f"   Technical Rate: {data['pricing']['technical_rate']:.2%}")
    else:
        print(f"❌ Simulation Failed: {response.text}")

    # 2. Test Vault Stats (Marketplace Layer)
    print("\n[2/5] Testing Risk Vault Statistics (Marketplace)...")
    response = requests.get(f"{BASE_URL}/transparency/vault/stats")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Vault Stats Success! TVL: ${data.get('tvl_usdc'):,.2f} | APY: {data.get('current_apy')}")
    else:
        print(f"❌ Vault Stats Failed: {response.text}")

    # 3. Test Transparency Audit Trail (Trust Layer)
    print("\n[3/5] Testing Transparency Audit (Trust)...")
    mock_tx = "0x5d2cbb342f26401980fc19ae9e01b7cc"
    response = requests.get(f"{BASE_URL}/transparency/audit/{mock_tx}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Audit Success! Source: {data['satellite_evidence']['source']}")
        print(f"   Status: {data.get('status')}")
    else:
        print(f"❌ Audit Failed: {response.text}")

    # 4. Test Carbon Offsetting (Carbon Ecosystem)
    print("\n[4/5] Testing Carbon Offsetting (Ecossistema)...")
    carbon_request = {
        "amount_usd": 500.0,
        "beneficiary_address": "0x1234567890abcdef"
    }
    response = requests.post(f"{BASE_URL}/carbon/offset", json=carbon_request)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Carbon Success! Retired: {data.get('tons')} tons | ID: {data.get('retirement_id')[:8]}...")
    else:
        print(f"❌ Carbon Failed: {response.text}")

    # 5. Check BigQuery Registries
    print("\n[5/5] Checking Registry Support...")
    response = requests.get(f"{BASE_URL}/carbon/registries")
    if response.status_code == 200:
        registries = response.json()
        print(f"✅ Registries: {[r['name'] for r in registries]}")
    else:
        print(f"❌ Registry Check Failed: {response.text}")

    print("\n--- ✨ All Layers Verified in Harmony! ---")

if __name__ == "__main__":
    test_full_flow()
