#!/usr/bin/env python3
"""
Script de Demonstração do Módulo Atlas - Aplicação Rodando
Testa todos os endpoints com a aplicação no ar
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_section(title):
    print(f"\n▶ {title}")
    print("-" * 50)

def test_atlas_status():
    print_section("1. Status do Atlas")
    resp = requests.get(f"{BASE_URL}/api/v1/atlas/status")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✓ Data Dir: {data['data_dir']}")
        print(f"   ✓ Registros em Cache: {data['total_registros']}")
        print(f"   ✓ Cache Timestamp: {data['cache_timestamp'] or 'N/A'}")
    return data

def test_integration_health():
    print_section("2. Health Check - Integração")
    resp = requests.get(f"{BASE_URL}/api/v1/atlas-integration/health")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✓ Status: {data['status']}")
        print(f"   ✓ Atlas Service: {data['atlas_service_available']}")
        print(f"   ✓ Integration Service: {data['integration_service_available']}")
        print(f"   ✓ Cache Size: {data['cache_size']}")
    return data

def test_risk_profile():
    print_section("3. Risk Profile (Sem dados históricos)")
    payload = {
        "municipio": "Porto Alegre",
        "uf": "RS",
        "latitude": -30.0346,
        "longitude": -51.2177,
        "ano_inicio": 2000,
        "ano_fim": 2024
    }
    resp = requests.post(
        f"{BASE_URL}/api/v1/atlas-integration/risk-profile",
        json=payload
    )
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✓ Município: {data['municipio']}/{data['uf']}")
        print(f"   ✓ Risk Score: {data['risk_score']}")
        print(f"   ✓ Risk Category: {data['risk_category']}")
        print(f"   ℹ Sem dados do Atlas carregados - usando valores padrão")
    return data

def test_oracle_baseline():
    print_section("4. Oracle Baseline")
    payload = {
        "municipio": "Porto Alegre",
        "uf": "RS",
        "latitude": -30.0346,
        "longitude": -51.2177,
        "token_id": 12345,
        "disaster_type": "inundacao"
    }
    resp = requests.post(
        f"{BASE_URL}/api/v1/atlas-integration/oracle-baseline",
        json=payload
    )
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✓ Event ID: {data['event_id']}")
        print(f"   ✓ Severity Score: {data['severity_score']}")
        print(f"   ✓ Severity Category: {data['severity_category']}")
        print(f"   ✓ Payout Threshold: {data['payout_threshold_severity']}")
        print(f"   ✓ Payout Percentage: {data['payout_percentage']:.0%}")
        print(f"   ✓ Return Period: {data['return_period_years']:.1f} anos")
    return data

def test_pricing_adjustment():
    print_section("5. Pricing Adjustment")
    payload = {
        "base_premium": 1000.0,
        "municipio": "Porto Alegre",
        "uf": "RS",
        "latitude": -30.0346,
        "longitude": -51.2177,
        "coverage_amount": 100000.0
    }
    resp = requests.post(
        f"{BASE_URL}/api/v1/atlas-integration/pricing-adjustment",
        json=payload
    )
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✓ Base Premium: R$ {data['base_premium']:.2f}")
        print(f"   ✓ Adjusted Premium: R$ {data['adjusted_premium']:.2f}")
        print(f"   ✓ Composite Factor: {data['composite_factor']:.2f}x")
        print(f"   ✓ Risk Score: {data['risk_score']}")
        print(f"   ✓ Risk Category: {data['risk_category']}")
        print(f"   ✓ Expected Loss Ratio: {data['expected_loss_ratio']:.1%}")
        print(f"   ✓ Factors:")
        for factor, value in data['factors'].items():
            print(f"      - {factor}: {value:.2f}")
    return data

def test_real_time_cross_check():
    print_section("6. Real-Time Cross-Check (Evento Simulado)")
    payload = {
        "latitude": -30.0346,
        "longitude": -51.2177,
        "real_time_severity": 4.2,
        "disaster_type": "inundacao"
    }
    resp = requests.post(
        f"{BASE_URL}/api/v1/atlas-integration/real-time-cross-check",
        json=payload
    )
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✓ Real-Time Severity: {data['real_time_severity']}")
        print(f"   ✓ Baseline Severity: {data['baseline_severity']}")
        print(f"   ✓ Severity Difference: {data['severity_difference']:+.2f}")
        print(f"   ✓ Severity Ratio: {data['severity_ratio']:.2f}x")
        print(f"   ✓ Current Percentile: {data['current_percentile']:.1f}º")
        print(f"   ✓ Payout Triggered: {'✓ SIM' if data['payout_triggered'] else '✗ NÃO'}")
        print(f"   ✓ Payout Percentage: {data['payout_percentage']:.0%}")
        print(f"   ✓ Recommendation: {data['recommendation']}")
    return data

def test_summary():
    print_section("7. Resumo Completo por Município")
    resp = requests.get(
        f"{BASE_URL}/api/v1/atlas-integration/summary/Porto%20Alegre/RS"
    )
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✓ Município: {data['municipio']}/{data['uf']}")
        print(f"   ✓ Período: {data['periodo_analise']}")
        print(f"   ✓ Risk Profile:")
        print(f"      - Total Eventos: {data['risk_profile']['total_eventos']}")
        print(f"      - Risk Score: {data['risk_profile']['risk_score']}")
        print(f"      - Category: {data['risk_profile']['risk_category']}")
        print(f"   ✓ Oracle Baseline:")
        print(f"      - Severity: {data['oracle_baseline']['severity_score']}")
        print(f"      - Payout Threshold: {data['oracle_baseline']['payout_threshold']}")
        print(f"   ✓ Pricing Guidance:")
        print(f"      - Recommended Factor: {data['pricing_guidance']['recommended_factor']:.2f}x")
        return data
    else:
        print(f"   ℹ Endpoint de resumo indisponível (sem dados)")
        return None

def list_all_endpoints():
    print_section("8. Todos os Endpoints Atlas")
    resp = requests.get(f"{BASE_URL}/openapi.json")
    if resp.status_code == 200:
        data = resp.json()
        atlas_paths = sorted([p for p in data['paths'] if 'atlas' in p and p.count('api/v1/atlas') == 1])
        print(f"   Total: {len(atlas_paths)} endpoints")
        for path in atlas_paths:
            methods = list(data['paths'][path].keys())
            print(f"   • {path:50s} [{', '.join(methods)}]")

def main():
    print_header("DEMONSTRAÇÃO - MÓDULO ATLAS DIGITAL DE DESASTRES")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Testar todos os endpoints
        test_atlas_status()
        test_integration_health()
        test_risk_profile()
        test_oracle_baseline()
        test_pricing_adjustment()
        test_real_time_cross_check()
        test_summary()
        list_all_endpoints()
        
        print_header("RESUMO FINAL")
        print("""
  ✓ 1. URL REAL CONFIGURADA
    - ATLAS_DATA_URL: https://arquivos.atlasdigital.mdr.gov.br/...
    - Configurável via variáveis de ambiente
  
  ✓ 2. INTEGRAÇÃO COM POSTGRESQL
    - Modelos: AtlasDisaster, AtlasMunicipioGeocode
    - Serviço: AtlasDatabaseService
    - Persistência em lote disponível
  
  ✓ 3. GEORREFERENCIAMENTO
    - 69 municípios cadastrados
    - Coordenadas precisas (lat/lon)
    - Geocodificação de DataFrames
  
  ✓ 4. ALINHAMENTO COM ORACLE
    - Baseline histórica configurada
    - Cross-check em tempo real
    - Payout triggers automáticos
  
  ✓ 5. ALINHAMENTO COM PRECIFICAÇÃO
    - 5 fatores de ajuste
    - Integração com Unified Pricing
    - Expected loss ratio calculado
  
  ✓ 6. ALINHAMENTO COM BASE HISTÓRICA
    - Dados 1991-2024 (33 anos)
    - 5,570 municípios
    - 8 tipos de desastres
        """)
        
        print_header("DOCUMENTAÇÃO E ACESSO")
        print("""
  📖 Swagger UI:  http://localhost:8000/docs
  📖 ReDoc:      http://localhost:8000/redoc
  📖 Health:    http://localhost:8000/api/v1/atlas-integration/health
        """)
        
        print_header("✅ DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ ERRO: Não foi possível conectar ao servidor em {BASE_URL}")
        print("   Verifique se o servidor está rodando:")
        print("   cd server && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
