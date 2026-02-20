#!/usr/bin/env python3
"""
Health check automatizado para o backend FastAPI
"""
import requests
import sys

BACKEND_URL = "http://localhost:8000/health"

def main():
    try:
        response = requests.get(BACKEND_URL, timeout=5)
        if response.status_code == 200:
            print(f"✅ Backend saudável: {response.json()}")
            sys.exit(0)
        else:
            print(f"❌ Backend respondeu, mas com status {response.status_code}: {response.text}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao conectar ao backend: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
