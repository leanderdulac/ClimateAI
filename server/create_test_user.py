#!/usr/bin/env python3
"""
Script para criar usuário de teste no Supabase
"""

import os
import requests
import json
import time

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR5em15d2h2cG1kZmVweGR0eWVzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg4NzAzNjcsImV4cCI6MjA4NDQ0NjM2N30.14R4jz5hzgx6u3pPnMDrnBEUmgorb0Iqlb8spQRgzaI"

def create_test_user():
    """Cria usuário de teste via Supabase Auth API"""
    
    url = f"{SUPABASE_URL}/auth/v1/signup"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    
    # Criar email único com timestamp
    timestamp = int(time.time())
    email = f"teste+{timestamp}@climatewise.com"
    
    payload = {
        "email": email,
        "password": "Teste123!",
        "data": {
            "full_name": "Usuário Teste",
            "company_name": "ClimateWise"
        }
    }
    
    print(f"Criando usuário de teste em: {url}")
    print(f"Email: {email}")
    print(f"Senha: Teste123!")
    print("-" * 50)
    
    response = requests.post(url, json=payload, headers=headers)
    result = response.json()
    
    if response.status_code in [200, 201]:
        print("✓ Usuário criado com sucesso!")
        print(f"\nID do usuário: {result.get('id', 'N/A')}")
        print(f"Email: {email}")
        print(f"Senha: Teste123!")
        print("\n⚠ IMPORTANTE: O email precisa ser confirmado.")
        print("Para testes, use o link de confirmação enviado por email.")
        print("\nOu use o comando curl abaixo para confirmar manualmente:")
        print(f"""
# Confirmar usuário manualmente (requer service_role key):
curl -X POST "{SUPABASE_URL}/auth/v1/admin/users" \\
  -H "Authorization: Bearer SERVICE_ROLE_KEY" \\
  -H "apikey: SERVICE_ROLE_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "email": "{email}",
    "password": "Teste123!",
    "email_confirm": true
  }}'
        """)
    elif response.status_code == 400:
        error = result
        print(f"⚠ Erro: {error.get('msg', 'Unknown error')}")
    else:
        print(f"✗ Erro: {response.status_code}")
        print(f"Response: {result}")

if __name__ == "__main__":
    create_test_user()
