import requests
import json

def test_cep(cep="29010001"):
    url = f"http://localhost:8000/api/v1/localizacao/cep/{cep}"
    print(f"Testing CEP: {cep}")
    print(f"URL: {url}")
    
    try:
        # Test OPTIONS first
        print("\n--- Testing OPTIONS (Preflight) ---")
        options_headers = {
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type"
        }
        try:
            res_opt = requests.options(url, headers=options_headers, timeout=5)
            print(f"OPTIONS Status: {res_opt.status_code}")
            print(f"CORS Headers: {dict(res_opt.headers)}")
        except requests.exceptions.Timeout:
            print("OPTIONS request timed out!")
        
        # Test GET
        print("\n--- Testing GET ---")
        try:
            res_get = requests.get(url, headers={"Origin": "http://localhost:5173"}, timeout=5)
            print(f"GET Status: {res_get.status_code}")
            print(f"Response: {json.dumps(res_get.json(), indent=2)}")
        except requests.exceptions.Timeout:
            print("GET request timed out!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cep()
