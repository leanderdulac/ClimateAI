#!/usr/bin/env python3
"""
Verificação Completa - ClimateWise Unified Platform
"""

import requests
import os
from datetime import datetime

print("=" * 70)
print("  VERIFICAÇÃO COMPLETA - CLIMATEWISE UNIFIED PLATFORM")
print("=" * 70)
print()

# 1. Backend
print("1. BACKEND (Porta 8000):")
try:
    r = requests.get("http://localhost:8000/health", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   ✓ Status: {data.get('status', 'N/A')}")
    else:
        print(f"   ❌ HTTP {r.status_code}")
except Exception as e:
    print(f"   ❌ Offline: {e}")

print()

# 2. Frontend
print("2. FRONTEND (Porta 5173):")
try:
    r = requests.get("http://localhost:5173/", timeout=5)
    print(f"   ✓ HTTP Status: {r.status_code}")
except Exception as e:
    print(f"   ❌ Offline: {e}")

print()

# 3. Endpoints Atlas/Space
print("3. ENDPOINTS ATLAS/SPACE:")
endpoints = [
    "/api/v1/atlas-simulation/health",
    "/api/v1/atlas-realtime/health",
    "/api/v1/unified-platform/health",
    "/api/v1/atlas-integration/health",
]

for ep in endpoints:
    try:
        r = requests.get(f"http://localhost:8000{ep}", timeout=5)
        status = "✓" if r.status_code == 200 else "❌"
        print(f"   {status} {ep}")
    except:
        print(f"   ❌ {ep} (offline)")

print()

# 4. Dados Integrados
print("4. DADOS INTEGRADOS (Unified Platform):")
try:
    r = requests.get("http://localhost:8000/api/v1/unified-platform/dashboard-summary", timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f"   ✓ Platform: {data.get('platform_status', 'N/A')}")
        layers = data.get('layers', {})
        for layer, info in layers.items():
            status = info.get('status', 'N/A')
            alerts = info.get('active_alerts', 0)
            print(f"   • {layer.upper()}: {status} ({alerts} alerts)")
        print(f"   ✓ Products: {data.get('products_available', 0)}")
    else:
        print(f"   ❌ HTTP {r.status_code}")
except Exception as e:
    print(f"   ❌ Erro: {e}")

print()

# 5. Arquivos de Integração
print("5. ARQUIVOS DE INTEGRAÇÃO:")
files = [
    "server/services/unified_earth_space_platform.py",
    "server/services/celestrak_service.py",
    "server/api/unified_platform.py",
    "client/src/components/AtlasDashboardPanel.tsx",
    "client/src/pages/AtlasPage.tsx",
]

for file in files:
    path = f"/home/exp/Downloads/ClimateAI/{file}"
    if os.path.exists(path):
        size = sum(1 for _ in open(path))
        print(f"   ✓ {file} ({size} linhas)")
    else:
        print(f"   ❌ {file} (não encontrado)")

print()
print("=" * 70)
print("  STATUS GERAL")
print("=" * 70)
print()
print(f"  Verificação concluída: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
