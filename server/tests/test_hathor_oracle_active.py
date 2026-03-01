import requests
import time
import json
from pprint import pprint

BASE_URL = "http://127.0.0.1:8000"

def test_active_blockchain_oracle():
    print("====================================")
    print("Testing Hathor Blockchain Activation")
    print("====================================")
    
    # 1. Create a Climate Token on Hathor
    print("\n1. Creating Climate Token via Hathor API...")
    create_token_payload = {
        "name": "CelesTrak Climate Token",
        "symbol": "CLMT",
        "total_supply": 1000000,
        "index_type": "temperature",
        "region": "Global Space",
        "latitude": 0.0,
        "longitude": 0.0,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "trigger_value": 3.0,
        "trigger_condition": "above",
        "payout_amount": 50000,
        "currency": "BRL",
        "oracle_source": "CelesTrak"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/v1/blockchain/hathor/api/v1/blockchain/hathor/tokens/create", json=create_token_payload)
        response.raise_for_status()
        token_data = response.json()
        print("✅ Hathor Token Creation Successful:")
        pprint(token_data)
        token_uid = token_data.get("token_uid", "0x0000")
    except Exception as e:
        print("❌ Hathor Token Creation Failed:", e)
        if hasattr(e, "response") and e.response:
            print(e.response.text)
        return

    print("\n====================================")
    print("Testing Climate Oracle Activation")
    print("====================================")
    
    # 2. Trigger an Oracle Severity Event
    print("\n2. Submitting Severity Event to Oracle (Severity 4.5 >= 3.0 threshold)...")
    oracle_payload = {
        "token_id": 9999, # Mocado pois o token Hathor é hash e o Oracle usa uint256
        "latitude": -23.5505,
        "longitude": -46.6333,
        "severity_score": 4.5,
        "ndvi": 0.45,
        "soil_moisture": 0.25,
        "source": "vertex_ai_celestrak"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/v1/oracle/evaluate", json=oracle_payload)
        response.raise_for_status()
        oracle_data = response.json()
        print("✅ Oracle Evaluation Successful:")
        pprint(oracle_data)
        if oracle_data.get("decision") == "TRIGGER_PAYOUT":
            print("→ Payout correctly triggered by Oracle logic!")
        else:
            print("→ Payout was NOT triggered.")
    except Exception as e:
        print("❌ Oracle Evaluation Failed:", e)
        if hasattr(e, "response") and e.response:
            print(e.response.text)

if __name__ == "__main__":
    # Wait for backend to fully start
    time.sleep(2)
    test_active_blockchain_oracle()
