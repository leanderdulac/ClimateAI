import requests
import json

payload = {
    "latitude": -23.55,
    "longitude": -46.63,
    "contract": {
        "area_id": "custom_sim",
        "start_date": "01-01",
        "end_date": "03-31",
        "trigger_mm": 100,
        "exhaustion_mm": 200,
        "max_payout": 1000000,
        "index_type": "max_3day"
    },
    "years_back": 20,
    "include_ep_curve": True
}

try:
    response = requests.post("http://127.0.0.1:8000/api/v1/parametric/simulate", json=payload, timeout=20)
    print("Status Code:", response.status_code)
    print("Response JSON:", json.dumps(response.json(), indent=2)[:1000])
except Exception as e:
    print("Error:", e)
