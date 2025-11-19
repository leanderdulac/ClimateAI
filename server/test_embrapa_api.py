#!/usr/bin/env python3
"""
Teste da integração com a API da Embrapa
"""
import asyncio
import os

from dotenv import load_dotenv

from services.embrapa_service import EmbrapaAPIService

# Carregar variáveis de ambiente
load_dotenv()


async def test_embrapa_api():
    """Testa a integração com a API da Embrapa"""

    print("🧪 Testando integração com API da Embrapa")
    print("=" * 50)

    # Inicializar serviço
    service = EmbrapaAPIService()

    print(f"✅ API Configurada: {service.is_configured}")
    print(f"📍 Base URL: {service.base_url}")
    print(f"🏷️  API Version: {service.api_version}")
    print(f"🔗 Full API URL: {service.base_url}/{service.api_version}")
    print()

    if not service.is_configured:
        print("⚠️  API Key não configurada. Configure EMBRAPA_API_KEY no arquivo .env")
        print("📖 Para obter uma chave de API, visite: https://www.embrapa.br/")
        return

    # Testar endpoints (se API key estiver configurada)
    print("🔍 Testando endpoints da API...")

    # Coordenadas de teste (São Paulo)
    latitude = -23.5505
    longitude = -46.6333

    try:
        # Testar dados históricos
        print("📊 Testando dados históricos...")
        historical_data = await service.get_climate_data(
            latitude=latitude,
            longitude=longitude,
            start_date="2023-01-01",
            end_date="2023-01-31",
        )
        print(f"✅ Dados históricos: {len(historical_data)} registros obtidos")

        # Testar previsão
        print("🌤️  Testando previsão do tempo...")
        forecast_data = await service.get_weather_forecast(
            latitude=latitude, longitude=longitude, days=3
        )
        print(f"✅ Previsão: {len(forecast_data.get('previsao', []))} dias previstos")

        # Testar localização
        print("📍 Testando geocodificação...")
        location_data = await service.get_location_data(latitude, longitude)
        print(f"✅ Localização: {location_data.get('cidade', 'N/A')}")

        print(
            "\n🎉 Todos os testes passaram! API da Embrapa está funcionando corretamente."
        )

    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        print(
            "💡 Verifique se a chave da API está correta e se você tem acesso aos endpoints."
        )


if __name__ == "__main__":
    asyncio.run(test_embrapa_api())
