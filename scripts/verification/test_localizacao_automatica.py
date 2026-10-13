import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1/localizacao"

def test_cep(cep="29010001"):
    url = f"{BASE_URL}/cep/{cep}"
    print(f"Testando CEP: {cep}")
    try:
        resp = requests.get(url, timeout=10)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Erro: {e}")

def test_city(city="Vitória", state=None):
    url = f"{BASE_URL}/cidade/{city}"
    params = {}
    if state:
        params["estado"] = state
    print(f"Testando cidade: {city} UF: {state}")
    try:
        resp = requests.get(url, params=params, timeout=10)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Erro: {e}")

def test_reverse_geocode(lat=-20.3155, lon=-40.3128):
    url = f"{BASE_URL}/coordenadas"
    params = {"latitude": lat, "longitude": lon}
    print(f"Testando reverse geocode: lat={lat}, lon={lon}")
    try:
        resp = requests.get(url, params=params, timeout=10)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    test_cep()
    test_city()
    test_city("São Paulo", "SP")
    test_reverse_geocode()