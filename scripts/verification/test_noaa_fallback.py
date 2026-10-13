#!/usr/bin/env python3
"""
Teste da integração NOAA com fallback para Embrapa
"""

import asyncio
import json
import requests
from datetime import datetime, timedelta

def test_noaa_fallback():
    """Testa o fallback NOAA -> Embrapa"""

    print("🧪 Testando fallback NOAA -> Embrapa")
    print("=" * 50)

    # Testar status
    try:
        response = requests.get("http://localhost:8002/api/v1/noaa/status")
        status_data = response.json()
        print(f"✅ Status: {status_data.get('status')}")
        print(f"   API Key configurada: {status_data.get('api_key_configured')}")
        print(f"   Mock mode: {status_data.get('mock_mode')}")
    except Exception as e:
        print(f"❌ Erro no status: {e}")
        return

    # Testar dados climáticos (deve falhar no NOAA e usar Embrapa)
    try:
        payload = {
            "location": "Localização Inexistente XYZ",
            "start_date": "2023-01-01",
            "end_date": "2023-01-05",
            "data_type": "TMAX"
        }
        response = requests.post(
            "http://localhost:8002/api/v1/noaa/climate-data",
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ Climate data endpoint: 200")
            print(f"   Localização: {data.get('location')}")
            print(f"   Latitude: {data.get('latitude')}")
            print(f"   Longitude: {data.get('longitude')}")
            print(f"   Fonte: {data.get('source')}")
            print(f"   Fallback usado: {data.get('fallback_used', False)}")
            print(f"   Número de resultados: {data.get('count')}")
            if data.get('fallback_used'):
                print("   🎉 Fallback Embrapa funcionou!")
                print(f"   Erro original: {data.get('original_error')}")
        else:
            print(f"❌ Climate data endpoint: {response.status_code}")
            print(f"   Erro: {response.text}")

    except Exception as e:
        print(f"❌ Erro nos dados climáticos: {e}")

    # Testar previsão do tempo
    try:
        payload = {
            "latitude": -23.5505,
            "longitude": -46.6333
        }
        response = requests.post(
            "http://localhost:8002/api/v1/noaa/weather-forecast",
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ Weather forecast endpoint: 200")
            print(f"   Latitude: {data.get('latitude')}")
            print(f"   Longitude: {data.get('longitude')}")
            print(f"   Fonte: {data.get('source')}")
            print(f"   Fallback usado: {data.get('fallback_used', False)}")
            forecast_count = len(data.get('forecast', []))
            print(f"   Períodos de previsão: {forecast_count}")
            if data.get('fallback_used'):
                print("   🎉 Fallback Embrapa funcionou!")
        else:
            print(f"❌ Weather forecast endpoint: {response.status_code}")
            print(f"   Erro: {response.text}")

    except Exception as e:
        print(f"❌ Erro na previsão: {e}")

    print("\n" + "=" * 50)
    print("🏆 Teste concluído!")

if __name__ == "__main__":
    test_noaa_fallback()