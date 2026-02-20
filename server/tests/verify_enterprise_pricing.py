
import pytest
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
# Use the API Key we generated earlier for auth
HEADERS = {
    "X-API-Key": "sk_live_3f4o5CpQ0Lvv3lcWF4Y1aTLfdp7i_fZA",
    "Content-Type": "application/json"
}

def test_valid_pricing_request():
    payload = {
        "latitude": -22.91,
        "longitude": -43.20,
        "contract": {
            "area_id": "rio_de_janeiro",
            "start_date": "01-01",
            "end_date": "03-31",
            "trigger_mm": 100.0,
            "exhaustion_mm": 200.0,
            "max_payout": 1000000.0,
            "index_type": "max_3day"
        },
        "years_back": 10,
        "include_ep_curve": True
    }
    
    response = requests.post(f"{BASE_URL}/parametric/simulate", headers=HEADERS, json=payload)
    print(f"Valid Request Status: {response.status_code}")
    if response.status_code != 200:
        print(response.text)
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "risk_metrics" in data
    assert "ep_curve" in data
    assert len(data["ep_curve"]["loss"]) > 0

def test_invalid_threshold_config():
    payload = {
        "latitude": -22.91,
        "longitude": -43.20,
        "contract": {
            "trigger_mm": 300.0, # Trigger > Exhaustion
            "exhaustion_mm": 200.0,
            "max_payout": 1000000.0
        },
        "years_back": 10
    }
    response = requests.post(f"{BASE_URL}/parametric/simulate", headers=HEADERS, json=payload)
    print(f"Invalid Config Status: {response.status_code}")
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_THRESHOLD_CONFIG"

def test_basis_risk_calculation():
    # Mock some actual losses that correlate with heavy rain
    # We don't know exactly which years rain fell, but let's send some dummy data
    actual_losses = [
        {"year": 2020, "loss_amount": 0.8},
        {"year": 2021, "loss_amount": 0.1},
        {"year": 2022, "loss_amount": 0.0},
        {"year": 2023, "loss_amount": 0.9}
    ]
    
    payload = {
        "latitude": -22.91,
        "longitude": -43.20,
        "contract": {
            "trigger_mm": 100.0,
            "exhaustion_mm": 200.0, 
            "max_payout": 1000000.0
        },
        "years_back": 5,
        "actual_losses": actual_losses
    }
    
    response = requests.post(f"{BASE_URL}/parametric/simulate", headers=HEADERS, json=payload)
    print(f"Basis Risk Status: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    assert "basis_risk" in data
    assert data["basis_risk"] is not None
    print("Basis Risk Metrics:", data["basis_risk"])

if __name__ == "__main__":
    try:
        test_valid_pricing_request()
        test_invalid_threshold_config()
        test_basis_risk_calculation()
        print("\nAll Enterprise Pricing Tests PASSED!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        exit(1)
