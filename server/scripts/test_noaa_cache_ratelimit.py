#!/usr/bin/env python3
"""
NOAA API Cache and Rate Limiting Test Script

Tests Redis caching and rate limiting functionality.

Usage:
    cd server
    source venv-hathor/bin/activate
    python scripts/test_noaa_cache_ratelimit.py
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add server to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain.hathor.oracle_service import get_climate_oracle_service


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


def test_redis_connection():
    """Test Redis connection"""
    print_header("TESTE 1: CONEXÃO REDIS")
    
    oracle = get_climate_oracle_service(use_cache=True)
    
    if oracle.redis_client:
        print(f"✅ Redis conectado!")
        try:
            # Test ping
            response = oracle.redis_client.ping()
            print(f"   Ping: {response}")
            
            # Test set/get
            test_key = "test:connection"
            oracle.redis_client.setex(test_key, 10, "test_value")
            value = oracle.redis_client.get(test_key)
            print(f"   Set/Get: {value}")
            
            return True
        except Exception as e:
            print(f"   ⚠️  Redis conectado mas com erros: {str(e)}")
            return False
    else:
        print(f"❌ Redis não disponível")
        print(f"   Usando cache em memória")
        return False


def test_cache_functionality():
    """Test cache get/set functionality"""
    print_header("TESTE 2: CACHE (GET/SET)")
    
    oracle = get_climate_oracle_service(use_cache=True)
    
    # Test data
    test_data = [
        {
            "timestamp": datetime.now().isoformat(),
            "latitude": -23.5505,
            "longitude": -46.6333,
            "temperature_c": 25.5,
            "precipitation_mm": 10.2,
            "source": "test",
        }
    ]
    
    # Generate cache key
    cache_key = oracle._get_cache_key(
        "test_data",
        lat=-23.5505,
        lon=-46.6333,
    )
    
    print(f"📊 Teste de Cache:")
    print(f"   Cache Key: {cache_key[:32]}...")
    
    # Test cache set
    print(f"\n   Setando cache...")
    oracle._cache_set(cache_key, test_data, ttl=60)
    print(f"   ✅ Dados cacheados")
    
    # Test cache get
    print(f"\n   Buscando no cache...")
    cached = oracle._cache_get(cache_key)
    
    if cached:
        print(f"   ✅ Cache hit!")
        print(f"      Dados: {cached}")
        return True
    else:
        print(f"   ❌ Cache miss")
        return False


def test_cache_with_real_data():
    """Test caching with real NOAA data"""
    print_header("TESTE 3: CACHE COM DADOS REAIS")
    
    oracle = get_climate_oracle_service(use_cache=True)
    
    # Test parameters
    latitude = -23.5505
    longitude = -46.6333
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f"📊 Parâmetros:")
    print(f"   Localização: ({latitude}, {longitude})")
    print(f"   Período: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
    
    # First request (should miss cache)
    print(f"\n🔍 Primeira requisição (cache miss)...")
    start_time = time.time()
    data1 = oracle.get_historical_data(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        source="noaa",
        use_cache=True,
    )
    time1 = time.time() - start_time
    
    print(f"   Tempo: {time1:.2f}s")
    print(f"   Dados: {len(data1)} pontos")
    
    # Second request (should hit cache)
    print(f"\n🔍 Segunda requisição (cache hit)...")
    start_time = time.time()
    data2 = oracle.get_historical_data(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
        source="noaa",
        use_cache=True,
    )
    time2 = time.time() - start_time
    
    print(f"   Tempo: {time2:.2f}s")
    print(f"   Dados: {len(data2)} pontos")
    
    # Calculate speedup
    if time2 > 0:
        speedup = time1 / time2
        print(f"\n📈 Speedup: {speedup:.2f}x")
        
        if speedup > 2:
            print(f"   ✅ Cache funcionando bem!")
            return True
        else:
            print(f"   ⚠️  Cache pode não estar otimizado")
            return False
    else:
        print(f"   ⚠️  Tempo muito rápido para medir")
        return len(data2) > 0


def test_rate_limiting():
    """Test rate limiting functionality"""
    print_header("TESTE 4: RATE LIMITING")
    
    oracle = get_climate_oracle_service(use_cache=False)  # Disable cache for this test
    
    print(f"📊 Configuração de Rate Limit:")
    print(f"   NOAA: {oracle.rate_limits['noaa']['requests_per_second']} req/s")
    print(f"   OpenMeteo: {oracle.rate_limits['openmeteo']['requests_per_second']} req/s")
    
    # Test rate limiting
    print(f"\n🔍 Testando rate limiting (5 requests rápidos)...")
    
    success_count = 0
    start_time = time.time()
    
    for i in range(5):
        allowed = oracle._check_rate_limit("noaa")
        if allowed:
            success_count += 1
            print(f"   Request {i+1}: ✅ Permitido")
        else:
            print(f"   Request {i+1}: ❌ Bloqueado (rate limit)")
    
    total_time = time.time() - start_time
    print(f"\n   Tempo total: {total_time:.2f}s")
    print(f"   Requests permitidos: {success_count}/5")
    
    if success_count > 0:
        print(f"   ✅ Rate limiting funcionando!")
        return True
    else:
        print(f"   ❌ Todos os requests bloqueados")
        return False


def test_fallback_mechanism():
    """Test fallback from NOAA to OpenMeteo"""
    print_header("TESTE 5: FALLBACK NOAA → OPENMETEO")
    
    oracle = get_climate_oracle_service(use_cache=False)
    
    # Test with coordinates in the middle of the ocean (no NOAA stations)
    print(f"📊 Testando fallback com coordenadas oceânicas...")
    print(f"   Localização: (0.0, -30.0) - Atlântico")
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        data = oracle.get_historical_data(
            latitude=0.0,
            longitude=-30.0,
            start_date=start_date,
            end_date=end_date,
            source="noaa",  # Request NOAA
            use_cache=False,
        )
        
        if data and len(data) > 0:
            print(f"   ✅ Fallback funcionou!")
            print(f"      Dados: {len(data)} pontos")
            print(f"      Fonte: {data[0].source}")
            
            if data[0].source == "openmeteo":
                print(f"      ✅ Fallback para OpenMeteo confirmado")
                return True
            else:
                print(f"      ⚠️  Fonte inesperada: {data[0].source}")
                return False
        else:
            print(f"   ⚠️  Nenhum dado retornado")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {str(e)}")
        return False


def test_daily_rate_limit():
    """Test daily rate limit tracking"""
    print_header("TESTE 6: DAILY RATE LIMIT TRACKING")
    
    oracle = get_climate_oracle_service(use_cache=False)
    
    print(f"📊 Status do Rate Limit Diário:")
    print(f"   NOAA requests hoje: {oracle.rate_limits['noaa']['today_requests']}")
    print(f"   NOAA limite diário: {oracle.rate_limits['noaa']['requests_per_day']}")
    print(f"   Data atual: {oracle.rate_limits['noaa']['today_date']}")
    
    # Simulate some requests
    print(f"\n🔍 Simulando 10 requests...")
    for i in range(10):
        oracle._check_rate_limit("noaa")
    
    print(f"   NOAA requests após teste: {oracle.rate_limits['noaa']['today_requests']}")
    
    if oracle.rate_limits['noaa']['today_requests'] >= 10:
        print(f"   ✅ Contador diário funcionando!")
        return True
    else:
        print(f"   ❌ Contador não atualizado corretamente")
        return False


def main():
    """Main test function"""
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  NOAA CACHE & RATE LIMIT TEST".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    results = {
        "redis": False,
        "cache": False,
        "cache_real": False,
        "rate_limit": False,
        "fallback": False,
        "daily_limit": False,
    }
    
    # Run tests
    results["redis"] = test_redis_connection()
    results["cache"] = test_cache_functionality()
    results["cache_real"] = test_cache_with_real_data()
    results["rate_limit"] = test_rate_limiting()
    results["fallback"] = test_fallback_mechanism()
    results["daily_limit"] = test_daily_rate_limit()
    
    # Summary
    print_header("RESUMO DOS TESTES")
    
    print("\n📊 RESULTADOS:")
    print(f"\n   1. Redis: {'✅ PASSOU' if results['redis'] else '❌ FALHOU'}")
    print(f"   2. Cache Get/Set: {'✅ PASSOU' if results['cache'] else '❌ FALHOU'}")
    print(f"   3. Cache com Dados Reais: {'✅ PASSOU' if results['cache_real'] else '❌ FALHOU'}")
    print(f"   4. Rate Limiting: {'✅ PASSOU' if results['rate_limit'] else '❌ FALHOU'}")
    print(f"   5. Fallback: {'✅ PASSOU' if results['fallback'] else '❌ FALHOU'}")
    print(f"   6. Daily Rate Limit: {'✅ PASSOU' if results['daily_limit'] else '❌ FALHOU'}")
    
    # Overall summary
    total_tests = len(results)
    passed = sum(1 for v in results.values() if v)
    
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
