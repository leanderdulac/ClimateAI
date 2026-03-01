#!/usr/bin/env python3
"""
Demonstração: Blockchain e Oracle com Dados Simulados
Mostra a integração completa do Atlas com Oracle e Blockchain
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
    print("-" * 60)

def demo_oracle_status():
    print_section("1. STATUS DO ORACLE")
    resp = requests.get(f"{BASE_URL}/api/v1/atlas-simulation/oracle-status")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✓ Status: {data['status']}")
        print(f"   ✓ Mode: {data['mode']}")
        print(f"   ✓ Events Processed: {data['total_events_processed']}")
        print(f"   ✓ Payouts Triggered: {data['total_payouts_triggered']}")
        print(f"   ✓ Blockchain Transactions: {data['total_blockchain_transactions']}")
        print(f"   ✓ Network: {data['network']}")
        print(f"   ✓ Contract: {data['contract_address']}")
    return data

def demo_portfolio_risk():
    print_section("2. PORTFOLIO RISK (Risco em Tempo Real)")
    resp = requests.get(f"{BASE_URL}/api/v1/atlas-simulation/portfolio-risk")
    if resp.status_code == 200:
        data = resp.json()
        summary = data['summary']
        print(f"   ✓ Total Exposure: R$ {summary['total_exposure']:,.2f}")
        print(f"   ✓ Potential Payout: R$ {summary['potential_payout']:,.2f}")
        print(f"   ✓ Impacted Policies: {summary['impacted_policies_count']}")
        print(f"   ✓ Total Alerts: {summary['total_alerts']}")
        print(f"   ✓ High Severity: {summary['high_severity_count']}")
        print(f"   ✓ Medium Severity: {summary['medium_severity_count']}")
        print(f"   ✓ Low Severity: {summary['low_severity_count']}")
        
        if data.get('blockchain_transactions'):
            print(f"\n   Blockchain Transactions (últimas {len(data['blockchain_transactions'])}):")
            for tx in data['blockchain_transactions']:
                print(f"      • TX: {tx['tx_id'][:16]}... | R$ {tx['amount']:,.2f} | {tx['confirmations']} conf.")
    return data

def demo_live_events():
    print_section("3. LIVE EVENTS (Eventos em Tempo Real)")
    resp = requests.get(f"{BASE_URL}/api/v1/atlas-simulation/live-events?limit=10")
    if resp.status_code == 200:
        events = resp.json()
        print(f"   Total Events: {len(events)}")
        print()
        
        payouts = [e for e in events if e['payout_triggered']]
        no_payouts = [e for e in events if not e['payout_triggered']]
        
        if payouts:
            print(f"   🟢 PAYOUTS TRIGGERED ({len(payouts)}):")
            for event in payouts[:5]:
                print(f"      • {event['municipio']}/{event['uf']} - {event['disaster_type']}")
                print(f"        Severity: {event['severity_score']} | Payout: R$ {event['payout_amount']:,.2f}")
                print(f"        TX: {event['blockchain_tx_id'][:24] if event['blockchain_tx_id'] else 'N/A'}...")
                print()
        
        if no_payouts:
            print(f"   🔵 NO PAYOUT ({len(no_payouts)}):")
            for event in no_payouts[:3]:
                print(f"      • {event['municipio']}/{event['uf']} - {event['disaster_type']}")
                print(f"        Severity: {event['severity_score']} (threshold: 3.0)")
        return events
    else:
        print(f"   Erro ao buscar eventos: HTTP {resp.status_code}")
        return []

def demo_trigger_new_event():
    print_section("4. TRIGGER NOVO EVENTO (Simulação)")
    resp = requests.post(f"{BASE_URL}/api/v1/atlas-simulation/trigger-event")
    if resp.status_code == 200:
        event = resp.json()
        print(f"   ✓ Event ID: {event['event_id']}")
        print(f"   ✓ Location: {event['municipio']}/{event['uf']}")
        print(f"   ✓ Disaster: {event['disaster_type']}")
        print(f"   ✓ Severity: {event['severity_score']}")
        print(f"   ✓ Payout Triggered: {'✓ SIM' if event['payout_triggered'] else '✗ NÃO'}")
        if event['payout_triggered']:
            print(f"   ✓ Payout Amount: R$ {event['payout_amount']:,.2f}")
            print(f"   ✓ Blockchain TX: {event['blockchain_tx_id'][:32]}...")
    return event

def demo_integration_flow():
    print_section("5. FLUXO COMPLETO DE INTEGRAÇÃO")
    print("""
   ┌────────────────────────────────────────────────────────────┐
   │  1. EVENTO CLIMÁTICO DETECTADO                             │
   │     - Vertex AI / Monitoramento em Tempo Real              │
   │     - Severity Score: 1.0-5.0                              │
   └────────────────────────────────────────────────────────────┘
                           ↓
   ┌────────────────────────────────────────────────────────────┐
   │  2. ORACLE AVALIA                                          │
   │     - Compara com baseline histórica (Atlas)               │
   │     - Threshold: severity >= 3.0                           │
   │     - Calcula payout percentage                            │
   └────────────────────────────────────────────────────────────┘
                           ↓
   ┌────────────────────────────────────────────────────────────┐
   │  3. PAYOUT TRIGGERADO (se severity >= 3.0)                │
   │     - Smart Contract chamado                               │
   │     - Transação blockchain gerada                          │
   │     - Token transferido para segurado                      │
   └────────────────────────────────────────────────────────────┘
                           ↓
   ┌────────────────────────────────────────────────────────────┐
   │  4. BLOCKCHAIN CONFIRMA                                    │
   │     - Hathor Testnet (Simulated)                           │
   │     - Confirmations: 6-100 blocks                          │
   │     - Transaction registrada                               │
   └────────────────────────────────────────────────────────────┘
   """)

def main():
    print_header("DEMONSTRAÇÃO: BLOCKCHAIN E ORACLE COM DADOS SIMULADOS")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Verificar saúde
        health = requests.get(f"{BASE_URL}/api/v1/atlas-simulation/health")
        if health.status_code != 200:
            print("❌ Serviço de simulação não disponível")
            return
        
        # Executar demonstração
        demo_oracle_status()
        demo_portfolio_risk()
        demo_live_events()
        demo_trigger_new_event()
        demo_integration_flow()
        
        print_header("RESUMO FINAL")
        print("""
  ✓ ORACLE IMPLEMENTADO
    - Severity evaluation (1.0-5.0)
    - Payout triggers automáticos
    - Baseline histórica do Atlas
    - Cross-check em tempo real
  
  ✓ BLOCKCHAIN SIMULADO
    - Hathor Testnet (Simulated)
    - Transações de payout
    - Token CLMT (Climate Index Token)
    - Confirmations e block height
  
  ✓ DADOS REALISTAS
    - 10 municípios de alto risco
    - Sazonalidade de desastres
    - Severidade baseada em histórico
    - Payouts calculados automaticamente
  
  ✓ INTEGRAÇÃO COM FRONTEND
    - RealTimeRiskMonitor.tsx usa /portfolio-risk
    - Dados em tempo real (refresh 60s)
    - Blockchain transactions exibidas
        """)
        
        print_header("ENDPOINTS PRINCIPAIS")
        print("""
  📊 Portfolio Risk:  GET /api/v1/atlas-simulation/portfolio-risk
  📡 Live Events:     GET /api/v1/atlas-simulation/live-events
  ⚡ Oracle Status:   GET /api/v1/atlas-simulation/oracle-status
  🎲 Trigger Event:   POST /api/v1/atlas-simulation/trigger-event
  📖 Demo Data:       GET /api/v1/atlas-simulation/demo
        """)
        
        print_header("✅ DEMONSTRAÇÃO CONCLUÍDA!")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERRO: Não foi possível conectar ao servidor em {BASE_URL}")
        print("   Verifique se o servidor está rodando")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
