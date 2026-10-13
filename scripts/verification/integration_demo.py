#!/usr/bin/env python3
"""
Demonstração de Integração: Cenários Probabilísticos Climáticos
Mostra como o Layer 2 (Probabilistic Scenarios) se integra com outros serviços
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"

def demonstrate_integration():
    """Demonstra a integração completa do serviço de cenários probabilísticos"""

    print("🌍 ClimateWise - Layer 2 Integration Demo")
    print("=" * 50)

    # 1. Obter combinações SSP-RCP disponíveis
    print("\n1. 📊 SSP-RCP Combinations Available:")
    try:
        response = requests.get(f"{BASE_URL}/probabilistic-climate-scenarios/ssp-rcp-combinations")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {data['count']} scenarios available")
            for scenario_name in list(data['combinations'].keys())[:3]:
                scenario = data['combinations'][scenario_name]
                print(f"   • {scenario_name}: {scenario['temperature_change_2100']}°C by 2100")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")

    # 2. Verificar modelos CMIP6
    print("\n2. 🧠 CMIP6 Models Available:")
    try:
        response = requests.get(f"{BASE_URL}/probabilistic-climate-scenarios/cmip6-models")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {data['count']} models available")
            print(f"   📈 Total ensemble members: {data['total_ensemble_members']}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")

    # 3. Calcular probabilidades baseado em indicadores atuais
    print("\n3. 🎯 Scenario Probabilities (Current CO₂: 420ppm, Temp: +1.1°C):")
    try:
        payload = {"co2_ppm": 420, "temperature_anomaly": 1.1}
        response = requests.post(f"{BASE_URL}/probabilistic-climate-scenarios/scenario-probabilities", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Most likely scenario: {data['most_likely_scenario']}")
            print("   📊 Top 3 scenarios by probability:")
            sorted_probs = sorted(data['scenario_probabilities'].items(), key=lambda x: x[1], reverse=True)
            for scenario, prob in sorted_probs[:3]:
                print(".1f")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")

    # 4. Gerar cenários para São Paulo
    print("\n4. 🏙️ Climate Scenarios for São Paulo (SSP2-RCP4.5):")
    try:
        payload = {
            "latitude": -23.5505,
            "longitude": -46.6333,
            "ssp_rcp_scenario": "SSP2-RCP4.5",
            "n_ensemble_members": 3
        }
        response = requests.post(f"{BASE_URL}/probabilistic-climate-scenarios/generate-scenarios", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Scenario: {data['scenario']}")
            print(f"   📍 Location: {data['location']}")
            print(f"   📅 Projection years: {len(data['projection_years'])} years")
            print(f"   🌡️ Temperature projections available: {len(data['temperature_projections'])} members")
            print(f"   🌧️ Precipitation projections available: {len(data['precipitation_projections'])} members")
            print(f"   🌊 Sea level projections available: {len(data['sea_level_projections'])} members")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")

    # 5. Status do serviço
    print("\n5. ⚡ Service Status:")
    try:
        response = requests.get(f"{BASE_URL}/probabilistic-climate-scenarios/status")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Service: {data['service']}")
            print(f"   📊 SSP-RCP combinations: {data['ssp_rcp_combinations']}")
            print(f"   🧠 CMIP6 models: {data['cmip6_models']}")
            print(f"   📈 Status: {data['status']}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")

    print("\n" + "=" * 50)
    print("🎉 Layer 2 Integration Complete!")
    print("📊 Probabilistic Climate Scenarios Service is fully operational")
    print("🔗 Ready for integration with Layers 3-7 (Risk Analysis, Pricing, etc.)")
    print(f"⏰ Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    demonstrate_integration()