import requests
import json

url = "http://localhost:8000/api/v1/clima/historico"
params = {
    "latitude": -20.3155,
    "longitude": -40.3436,
    "data_inicio": "2026-01-16",
    "data_fim": "2026-02-15"
}

response = requests.get(url, params=params)
print(f"Status Code: {response.status_code}")
try:
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except:
    print(f"Raw Response: {response.text}")
