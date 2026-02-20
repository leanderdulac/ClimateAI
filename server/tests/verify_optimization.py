
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "X-API-Key": "sk_live_3f4o5CpQ0Lvv3lcWF4Y1aTLfdp7i_fZA",
    "Content-Type": "application/json"
}

def test_optimization():
    print("Testing Optimization Endpoint...")
    
    # Mock losses where 2020 and 2023 were bad years
    actual_losses = [
        {"year": 2020, "loss_amount": 0.9},
        {"year": 2021, "loss_amount": 0.0},
        {"year": 2022, "loss_amount": 0.0},
        {"year": 2023, "loss_amount": 0.8},
        {"year": 2024, "loss_amount": 0.0},
    ]
    
    payload = {
        "latitude": -22.91,
        "longitude": -43.20,
        "years_back": 10,
        "constraints": {
            "min_aal": 10000.0, # 1% of 1M
            "max_aal": 300000.0 # 30% of 1M
        },
        "actual_losses": actual_losses,
        "trigger_min": 50.0,
        "trigger_max": 150.0,
        "trigger_step": 25.0,
        "exhaustion_add_min": 50.0,
        "exhaustion_add_max": 200.0,
        "exhaustion_add_step": 50.0
    }
    
    start_time = time.time()
    response = requests.post(f"{BASE_URL}/parametric/optimize", headers=HEADERS, json=payload)
    duration = time.time() - start_time
    
    print(f"Status: {response.status_code}")
    print(f"Duration: {duration:.2f}s")
    
    if response.status_code != 200:
        print("Error:", response.text)
        return

    results = response.json()
    print(f"Found {len(results)} configurations.")
    
    if len(results) > 0:
        best = results[0]
        print(f"Best Config: Trigger={best['trigger_mm']}mm, Exhaustion={best['exhaustion_mm']}mm")
        print(f"Metrics: AAL={best['aal']}, FN Rate={best['false_negative_rate']:.2f}, FP Rate={best['false_positive_rate']:.2f}")
        
        # Validation
        assert best['false_negative_rate'] <= results[-1]['false_negative_rate'] # Should be sorted
        assert best['aal'] >= 10000.0

if __name__ == "__main__":
    try:
        test_optimization()
    except Exception as e:
        print(f"TEST FAILED: {e}")
        exit(1)
