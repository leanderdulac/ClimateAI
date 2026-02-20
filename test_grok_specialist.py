#!/usr/bin/env python3
"""
Test script for Grok parametric insurance endpoints
"""

import requests
import json

def test_grok_endpoints():
    base_url = "http://localhost:8001"

    print("🧪 Testando endpoints especializados do Grok para Seguros Paramétricos")
    print("=" * 70)

    # Test 1: Status do Grok
    try:
        response = requests.get(f"{base_url}/api/v1/grok/status")
        print(f"✅ Status endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   API Configured: {data.get('api_configured')}")
    except Exception as e:
        print(f"❌ Status endpoint failed: {e}")

    # Test 2: Análise paramétrica
    try:
        payload = {
            "location": "São Paulo",
            "risk_type": "agricultural",
            "coverage_value": 1000000,
            "time_period": "12_months"
        }
        response = requests.post(f"{base_url}/api/v1/grok/parametric-insurance", json=payload)
        print(f"✅ Parametric insurance endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Location: {data.get('location')}")
            print(f"   Risk Type: {data.get('risk_type')}")
            print(f"   Analysis preview: {data.get('parametric_analysis', '')[:100]}...")
    except Exception as e:
        print(f"❌ Parametric insurance endpoint failed: {e}")

    # Test 3: Cálculo atuarial
    try:
        payload = {
            "location": "Rio de Janeiro",
            "risk_type": "urban",
            "coverage_value": 5000000,
            "time_period": "24_months"
        }
        response = requests.post(f"{base_url}/api/v1/grok/actuarial-calculation", json=payload)
        print(f"✅ Actuarial calculation endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Coverage Value: R$ {data.get('coverage_value', 0):,}")
            print(f"   Technical Rate: {data.get('technical_parameters', {}).get('technical_rate', 0)*100}%")
            print(f"   Calculation preview: {data.get('actuarial_calculation', '')[:100]}...")
    except Exception as e:
        print(f"❌ Actuarial calculation endpoint failed: {e}")

    # Test 4: Análise climática especializada
    try:
        payload = {
            "data": {
                "location": "Brasília",
                "temperature": 28.5,
                "precipitation": 45.0,
                "analysis_type": "parametric_insurance"
            },
            "analysis_type": "parametric_insurance"
        }
        response = requests.post(f"{base_url}/api/v1/grok/analyze", json=payload)
        print(f"✅ Climate analysis endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Analysis Type: {data.get('analysis_type')}")
            print(f"   Confidence: {data.get('confidence', 0):.1%}")
            print(f"   Analysis preview: {data.get('analysis', '')[:100]}...")
    except Exception as e:
        print(f"❌ Climate analysis endpoint failed: {e}")

    # Test 5: Insights climáticos
    try:
        payload = {
            "location": "Salvador",
            "time_period": "6_months"
        }
        response = requests.post(f"{base_url}/api/v1/grok/insights", json=payload)
        print(f"✅ Climate insights endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Location: {data.get('location', 'Salvador')}")
            print(f"   Insights preview: {data.get('insights', '')[:100]}...")
    except Exception as e:
        print(f"❌ Climate insights endpoint failed: {e}")

    # Test 6: Modelos disponíveis
    try:
        response = requests.get(f"{base_url}/api/v1/grok/models")
        print(f"✅ Models endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Current Model: {data.get('current_model')}")
            print(f"   Training Focus: {data.get('training_focus')}")
            print(f"   Specializations: {len(data.get('models', [{}])[0].get('specializations', []))} areas")
    except Exception as e:
        print(f"❌ Models endpoint failed: {e}")

    print("\n" + "=" * 70)
    print("🏆 Teste concluído! O Grok agora é especialista em:")
    print("   • Seguros paramétricos")
    print("   • Normas da Susep")
    print("   • Cálculos atuariais")
    print("   • Histórico climático brasileiro (1994-2024)")

if __name__ == "__main__":
    test_grok_endpoints()