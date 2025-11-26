import http.client
import os
import threading
import time

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Define the app structure
app = FastAPI()

# Simulate environment variable
os.environ["ALLOW_ORIGINS"] = "http://localhost:3000,https://myapp.com"

# Configuration logic from main.py
allow_origins_str = os.getenv("ALLOW_ORIGINS", "*")
allow_origins = allow_origins_str.split(",") if allow_origins_str != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="error")


def test_cors():
    # Start server in a thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Wait for server to start

    print("--- Testing Allowed Origin (http://localhost:3000) ---")
    conn = http.client.HTTPConnection("127.0.0.1", 8002)
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    }
    conn.request("OPTIONS", "/", headers=headers)
    response = conn.getresponse()

    acao = response.getheader("access-control-allow-origin")
    print(f"Status: {response.status}")
    print(f"Access-Control-Allow-Origin: {acao}")

    if acao == "http://localhost:3000":
        print("SUCCESS: Allowed origin correctly handled.")
    else:
        print("FAILURE: Allowed origin not handled correctly.")
    conn.close()

    print("\n--- Testing Disallowed Origin (http://malicious-site.com) ---")
    conn = http.client.HTTPConnection("127.0.0.1", 8002)
    headers = {
        "Origin": "http://malicious-site.com",
        "Access-Control-Request-Method": "GET",
    }
    conn.request("OPTIONS", "/", headers=headers)
    response = conn.getresponse()

    acao = response.getheader("access-control-allow-origin")
    print(f"Status: {response.status}")
    print(f"Access-Control-Allow-Origin: {acao}")

    if acao is None:
        print("SUCCESS: Disallowed origin correctly blocked (no header returned).")
    else:
        print("FAILURE: Disallowed origin should not have access-control header.")
    conn.close()


if __name__ == "__main__":
    test_cors()
