#!/usr/bin/env python3
"""
NOAA API Test Script - Brazilian Stations

Tests NOAA CDO API integration with real weather stations in Brazil.
Verifies data quality, coverage, and API functionality.

Usage:
    cd server
    source venv-hathor/bin/activate
    python scripts/test_noaa_brazil_stations.py
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add server to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain.hathor.oracle_service import get_climate_oracle_service
from blockchain.hathor.config import get_hathor_config


# Brazilian cities with known NOAA stations
BRAZIL_CITIES = [
    {
        "name": "São Paulo",
        "latitude": -23.5505,
        "longitude": -46.6333,
        "expected_station": "GHCND:BR001000",
    },
    {
        "name": "Rio de Janeiro",
        "latitude": -22.9068,
        "longitude": -43.1729,
        "expected_station": "GHCND:BR001001",
    },
    {
        "name": "Brasília",
        "latitude": -15.7801,
        "longitude": -47.9292,
        "expected_station": "GHCND:BR001002",
    },
    {
        "name": "Salvador",
        "latitude": -12.9714,
        "longitude": -38.5014,
        "expected_station": "GHCND:BR001003",
    },
    {
        "name": "Fortaleza",
        "latitude": -3.7319,
        "longitude": -38.5267,
        "expected_station": "GHCND:BR001004",
    },
    {
        "name": "Manaus",
        "latitude": -3.1190,
        "longitude": -60.0217,
        "expected_station": "GHCND:BR001005",
    },
    {
        "name": "Curitiba",
        "latitude": -25.4284,
        "longitude": -49.2733,
        "expected_station": None,  # May not have station
    },
    {
        "name": "Recife",
        "latitude": -8.0476,
        "longitude": -34.8770,
        "expected_station": None,
    },
]


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_section(title: str):
    """Print section header"""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")


def test_noaa_connection():
    """Test basic NOAA API connectivity"""
    print_header("TESTE 1: CONEXÃO COM NOAA API")
    
    oracle = get_climate_oracle_service()
    config = get_hathor_config()
    
    print(f"📊 Configuração:")
    print(f"   NOAA API Key: {oracle.noaa_token[:20]}...")
    print(f"   NOAA Base URL: {oracle.noaa_base_url}")
    print(f"   Hathor Network: {config.NETWORK}")
    
    # Test API token validity with a simple request
    try:
        import requests
        test_url = f"{oracle.noaa_base_url}/datasets?limit=1"
        headers = {"token": oracle.noaa_token}
        
        print(f"\n🔍 Testando conexão...")
        response = requests.get(test_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print(f"   ✅ Conexão bem-sucedida!")
            print(f"   Status Code: {response.status_code}")
            data = response.json()
            if data.get("results"):
                print(f"   Datasets disponíveis: {len(data.get('results', []))}")
            return True
        elif response.status_code == 401:
            print(f"   ❌ Erro de autenticação (401)")
            print(f"   Verifique a API key: {oracle.noaa_token}")
            return False
        elif response.status_code == 429:
            print(f"   ⚠️  Rate limit excedido (429)")
            print(f"   Aguarde antes de tentar novamente")
            return False
        else:
            print(f"   ⚠️  Erro HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ❌ Timeout na conexão (30s)")
        return False
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False


def test_station_search(city_data: Dict[str, Any]) -> bool:
    """Test station search for a specific city"""
    print(f"\n📍 Testando: {city_data['name']}")
    print(f"   Coordenadas: ({city_data['latitude']}, {city_data['longitude']})")
    
    oracle = get_climate_oracle_service()
    
    try:
        import requests
        
        # Search for stations within bounding box
        lat_range = 0.5
        lon_range = 0.5
        extent = f"{city_data['latitude']-lat_range},{city_data['longitude']-lon_range},{city_data['latitude']+lat_range},{city_data['longitude']+lon_range}"
        
        stations_url = f"{oracle.noaa_base_url}/stations"
        params = {
            "limit": 10,
            "extent": extent,
        }
        headers = {"token": oracle.noaa_token}
        
        response = requests.get(stations_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        stations = data.get("results", [])
        
        if not stations:
            print(f"   ❌ Nenhuma estação encontrada")
            return False
        
        print(f"   ✅ {len(stations)} estação(ões) encontrada(s)")
        
        # Print station details
        for i, station in enumerate(stations[:3], 1):
            print(f"\n   Estação {i}:")
            print(f"      ID: {station.get('id', 'N/A')}")
            print(f"      Nome: {station.get('name', 'N/A')}")
            print(f"      Localização: ({station.get('latitude', 'N/A')}, {station.get('longitude', 'N/A')})")
            print(f"      Elevação: {station.get('elevation', 'N/A')} m")
            print(f"      Período: {station.get('mindate', 'N/A')} a {station.get('maxdate', 'N/A')}")
            print(f"      Cobertura: {station.get('datacoverage', 0):.0%}")
            
            # Check if matches expected station
            if city_data.get('expected_station'):
                if station.get('id') == city_data['expected_station']:
                    print(f"      ✅ Estação esperada encontrada!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False


def test_data_fetch(city_data: Dict[str, Any], station_id: str) -> bool:
    """Test data fetch from a specific station"""
    print(f"\n📊 Testando fetch de dados: {city_data['name']}")
    print(f"   Estação: {station_id}")
    
    oracle = get_climate_oracle_service()
    
    try:
        import requests
        
        # Fetch last 30 days of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        data_url = f"{oracle.noaa_base_url}/data"
        params = {
            "datasetid": "GHCND",
            "stationid": station_id,
            "startdate": start_date.strftime("%Y-%m-%d"),
            "enddate": end_date.strftime("%Y-%m-%d"),
            "units": "metric",
            "limit": 1000,
            "includemetadata": "false",
        }
        headers = {"token": oracle.noaa_token}
        
        print(f"   Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
        
        response = requests.get(data_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            print(f"   ⚠️  Nenhum dado disponível para este período")
            return False
        
        print(f"   ✅ {len(results)} registros encontrados")
        
        # Analyze data types
        datatypes = {}
        for result in results:
            dt = result.get("datatype", "UNKNOWN")
            datatypes[dt] = datatypes.get(dt, 0) + 1
        
        print(f"\n   Tipos de dados:")
        for dt, count in sorted(datatypes.items()):
            print(f"      {dt}: {count} registros")
        
        # Check data quality
        dates = set()
        for result in results:
            date_str = result.get("date", "")[:10]
            dates.add(date_str)
        
        print(f"\n   Qualidade dos dados:")
        print(f"      Dias com dados: {len(dates)}")
        print(f"      Período coberto: {min(dates) if dates else 'N/A'} a {max(dates) if dates else 'N/A'}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False


def test_oracle_service(city_data: Dict[str, Any]) -> bool:
    """Test full oracle service integration"""
    print(f"\n🔧 Testando Oracle Service: {city_data['name']}")
    
    oracle = get_climate_oracle_service()
    
    try:
        # Get historical data via oracle service
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"   Buscando dados históricos...")
        data_points = oracle.get_historical_data(
            latitude=city_data['latitude'],
            longitude=city_data['longitude'],
            start_date=start_date,
            end_date=end_date,
            source="noaa",
        )
        
        if not data_points:
            print(f"   ❌ Nenhum dado retornado")
            return False
        
        print(f"   ✅ {len(data_points)} pontos de dados obtidos")
        
        # Analyze data quality
        temp_values = [p.temperature_c for p in data_points if p.temperature_c is not None]
        precip_values = [p.precipitation_mm for p in data_points if p.precipitation_mm is not None]
        
        print(f"\n   Análise dos dados:")
        if temp_values:
            print(f"      Temperatura: {min(temp_values):.1f}°C a {max(temp_values):.1f}°C (média: {sum(temp_values)/len(temp_values):.1f}°C)")
        else:
            print(f"      Temperatura: Sem dados")
            
        if precip_values:
            print(f"      Precipitação: {min(precip_values):.1f}mm a {max(precip_values):.1f}mm (total: {sum(precip_values):.1f}mm)")
        else:
            print(f"      Precipitação: Sem dados")
        
        # Calculate indices
        if precip_values:
            total_precip = oracle.calculate_precipitation_index(data_points, "sum")
            print(f"\n   Índices calculados:")
            print(f"      Precipitação total (30 dias): {total_precip:.1f}mm")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_fallback_to_openmeteo(city_data: Dict[str, Any]) -> bool:
    """Test fallback to OpenMeteo when NOAA fails"""
    print(f"\n🔄 Testando Fallback NOAA → OpenMeteo: {city_data['name']}")
    
    oracle = get_climate_oracle_service()
    
    try:
        # Force NOAA to fail by using invalid coordinates (ocean)
        print(f"   Forçando fallback com coordenadas inválidas...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Ocean coordinates (no stations expected)
        data_points = oracle.get_historical_data(
            latitude=0.0,
            longitude=-30.0,  # Middle of Atlantic
            start_date=start_date,
            end_date=end_date,
            source="noaa",
        )
        
        if data_points and len(data_points) > 0:
            print(f"   ✅ Fallback funcionou: {len(data_points)} pontos de OpenMeteo")
            print(f"      Fonte: {data_points[0].source}")
            return True
        else:
            print(f"   ⚠️  Fallback não retornou dados")
            return False
        
    except Exception as e:
        print(f"   ❌ Erro no fallback: {str(e)}")
        return False


def main():
    """Main test function"""
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  NOAA API TEST SUITE".center(78) + "█")
    print("█" + "  Testes com Estações Reais no Brasil".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    results = {
        "connection": False,
        "stations": [],
        "data_fetch": [],
        "oracle_service": [],
        "fallback": False,
    }
    
    # Test 1: Basic connection
    results["connection"] = test_noaa_connection()
    
    if not results["connection"]:
        print("\n⚠️  Conexão NOAA falhou. Testes subsequentes podem falhar.")
        print("   Verifique a API key e conexão de internet.")
    
    # Test 2: Station search for each city
    print_header("TESTE 2: BUSCA DE ESTAÇÕES")
    for city in BRAZIL_CITIES:
        success = test_station_search(city)
        results["stations"].append((city["name"], success))
    
    # Test 3: Data fetch from known stations
    print_header("TESTE 3: FETCH DE DADOS")
    for city in BRAZIL_CITIES[:3]:  # Test first 3 cities
        if city.get("expected_station"):
            success = test_data_fetch(city, city["expected_station"])
            results["data_fetch"].append((city["name"], success))
    
    # Test 4: Full oracle service integration
    print_header("TESTE 4: ORACLE SERVICE")
    for city in BRAZIL_CITIES[:3]:  # Test first 3 cities
        success = test_oracle_service(city)
        results["oracle_service"].append((city["name"], success))
    
    # Test 5: Fallback mechanism
    print_header("TESTE 5: FALLBACK NOAA → OPENMETEO")
    results["fallback"] = test_fallback_to_openmeteo(BRAZIL_CITIES[0])
    
    # Summary
    print_header("RESUMO DOS TESTES")
    
    print("\n📊 RESULTADOS:")
    print(f"\n   1. Conexão NOAA: {'✅ PASSOU' if results['connection'] else '❌ FALHOU'}")
    
    print(f"\n   2. Busca de Estações:")
    for city, success in results["stations"]:
        status = "✅" if success else "❌"
        print(f"      {status} {city}")
    
    print(f"\n   3. Fetch de Dados:")
    for city, success in results["data_fetch"]:
        status = "✅" if success else "❌"
        print(f"      {status} {city}")
    
    print(f"\n   4. Oracle Service:")
    for city, success in results["oracle_service"]:
        status = "✅" if success else "❌"
        print(f"      {status} {city}")
    
    print(f"\n   5. Fallback: {'✅ PASSOU' if results['fallback'] else '❌ FALHOU'}")
    
    # Overall summary
    total_tests = 1 + len(results["stations"]) + len(results["data_fetch"]) + len(results["oracle_service"]) + 1
    passed = sum([
        1 if results["connection"] else 0,
        sum(1 for _, s in results["stations"] if s),
        sum(1 for _, s in results["data_fetch"] if s),
        sum(1 for _, s in results["oracle_service"] if s),
        1 if results["fallback"] else 0,
    ])
    
    print(f"\n{'═' * 60}")
    print(f"  TOTAL: {passed}/{total_tests} testes passaram ({passed/total_tests*100:.1f}%)")
    print(f"{'═' * 60}")
    
    if passed == total_tests:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
    elif passed >= total_tests * 0.8:
        print("\n✅ MAIORIA DOS TESTES PASSOU!")
    else:
        print("\n⚠️  VÁRIOS TESTES FALHARAM - VERIFIQUE A CONFIGURAÇÃO")
    
    print("\n" + "█" * 80)
    print("█" + "  TEST SUITE COMPLETED".center(78) + "█")
    print("█" * 80 + "\n")


if __name__ == "__main__":
    main()
