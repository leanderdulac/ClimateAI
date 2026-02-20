
import requests
import uuid

BASE_URL = "http://127.0.0.1:8000"

def test_auth_flow():
    email = f"test.user.{uuid.uuid4().hex[:8]}@example.com"
    password = "password123"
    full_name = "Test User Registration"
    
    print(f"Testing registration for {email}...")
    register_payload = {
        "email": email,
        "password": password,
        "full_name": full_name,
        "role": "user",
        "organization": "Test Org"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_payload)
    print(f"Registration status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
        
    print(f"Registration success: {response.json()}")
    
    print(f"Testing login for {email}...")
    login_payload = {
        "email": email,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_payload)
    print(f"Login status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return
        
    print(f"Login success: {response.json().get('access_token')[:20]}...")

if __name__ == "__main__":
    test_auth_flow()
