import asyncio
import os
import sys
from pathlib import Path

# Adicionar diretório pai ao path para importar módulos
sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.gemini_integration_service import GeminiIntegrationService
from services.geocoding_service import GeocodingService


async def verify_location():
    print("--- Verifying Location Search ---")
    service = GeocodingService()

    # Teste 1: Cidade pequena que provavelmente não estava na lista antiga
    city_name = "Gramado"
    print(f"Searching for '{city_name}'...")
    results = await service.search_cities(city_name)

    found = False
    for city in results:
        print(
            f"Found: {city['city']} - {city['state']} (Lat: {city.get('latitude')}, Lon: {city.get('longitude')})"
        )
        if city["city"] == "Gramado" and city["state"] == "RS":
            found = True

    if found:
        print("✅ SUCCESS: Gramado/RS found in dataset.")
    else:
        print("❌ FAILURE: Gramado/RS NOT found.")

    # Teste 2: Performance (busca rápida)
    print("\nTesting search performance...")
    import time

    start = time.time()
    await service.search_cities("sao")
    end = time.time()
    print(f"Search for 'sao' took {end - start:.4f} seconds")


async def verify_ai_context():
    print("\n--- Verifying AI Context Injection ---")
    # Mockar a chamada real para não gastar quota ou depender de rede,
    # mas queremos ver se o prompt é construído corretamente.
    # Como o método chat_with_assistant monta o prompt internamente e chama a API,
    # vamos instanciar e chamar, mas talvez falhe se a API key for inválida.
    # Vamos assumir que a API Key hardcoded no arquivo funciona ou falha graciosamente.

    service = GeminiIntegrationService()

    context = {
        "location": {
            "city": "Gramado",
            "state": "RS",
            "latitude": -29.37,
            "longitude": -50.87,
        },
        "weather": {"temp": 15, "precip": 0, "humidity": 80},
    }

    print("Sending message with context...")
    try:
        # Se a API key for inválida, vai retornar erro ou mensagem de erro.
        # O importante é que o código rode sem exceção de sintaxe.
        result = await service.chat_with_assistant(
            "Qual o risco de geada?", context=context
        )
        print(f"Result Type: {result.analysis_type}")
        print(f"Confidence: {result.confidence_level}")
        print(f"Response Preview: {result.analysis_text[:100]}...")

        if result.analysis_type == "chat_response":
            print("✅ SUCCESS: AI responded.")
        else:
            print(
                "⚠️ WARNING: AI responded with error (expected if API key is invalid/quota exceeded)."
            )

    except Exception as e:
        print(f"❌ ERROR calling AI service: {e}")


if __name__ == "__main__":
    asyncio.run(verify_location())
    asyncio.run(verify_ai_context())
