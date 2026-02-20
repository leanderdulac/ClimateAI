
import asyncio
import os
from services.noaa_service import NOAAService
from config.config import settings
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Force reload of .env
load_dotenv(override=True)

# Update settings object if it was already loaded
if os.getenv("NOAA_API_KEY"):
    settings.NOAA_API_KEY = os.getenv("NOAA_API_KEY")

async def test_noaa():
    print(f"Iniciando teste do NOAA... Key configured: {bool(settings.NOAA_API_KEY)}")
    
    try:
        service = NOAAService()
        
        # Using a known location (New York for global data or a US location as NOAA is US-centric)
        # NOAA CDO data is global but station coverage varies. 
        # Using "FIPS:06" (California) or just a lat/lon query if supported.
        # But NOAAService.get_climate_data takes 'location' string and geocodes it.
        # I'll mock the geocoding to avoid another dependency failure if possible, 
        # but NOAAService uses GeocodingService.
        
        # Let's try a direct simple call if possible or just use the service as is.
        # Location: "Miami, FL"
        location = "Miami, FL"
        start_date = "2023-01-01"
        end_date = "2023-01-07"
        
        print(f"Buscando dados para {location} de {start_date} a {end_date}")
        data = await service.get_climate_data(location, start_date, end_date)
        
        if data:
            print(f"Resultado: {data.get('source')}")
            if "results" in data and data["results"]:
                print(f"Sucesso! Recebidos {len(data['results'])} registros.")
                print(f"Exemplo: {data['results'][0]}")
            else:
                print("Aviso: Retorno vazio ou erro (verifique se source é Mock).")
                print(data)
        else:
            print("Falha: Retorno None.")

    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_noaa())
