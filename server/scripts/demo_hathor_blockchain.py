#!/usr/bin/env python3
"""
Hathor Blockchain Demo Script

Demonstrates climate token creation and management on Hathor Network.
Runs in development mode (mock) - integrate with real wallet for production.

Usage:
    cd server
    source venv-hathor/bin/activate
    python scripts/demo_hathor_blockchain.py
"""

import sys
import os

# Add server to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from blockchain.hathor.config import get_hathor_config
from blockchain.hathor.hathor_service import get_hathor_service
from blockchain.hathor.climate_token_service import (
    get_climate_token_service,
    ClimateTokenMetadata,
    ClimateIndexType,
)
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


def demo_hathor_initialization():
    """Demonstrate Hathor wallet initialization"""
    print_header("1. INICIALIZAÇÃO DA HATHOR BLOCKCHAIN")
    
    config = get_hathor_config()
    print(f"📊 Configuração:")
    print(f"   Rede: {config.NETWORK}")
    print(f"   RPC URL: {config.rpc_url}")
    print(f"   Explorer: {config.explorer_url}")
    
    hathor = get_hathor_service()
    
    # Initialize wallet (development mode)
    print("\n🔑 Inicializando wallet...")
    address = hathor.initialize(address="dev_wallet_placeholder_address")
    print(f"   Wallet address: {address}")
    print(f"   Status: {'✅ Inicializado' if hathor._initialized else '❌ Falhou'}")
    
    return hathor


def demo_token_creation():
    """Demonstrate climate token creation"""
    print_header("2. CRIAÇÃO DE TOKEN CLIMÁTICO")
    
    token_service = get_climate_token_service()
    
    # Create drought token metadata
    print("📝 Criando token de seca (Drought Index)...")
    metadata = ClimateTokenMetadata(
        index_type=ClimateIndexType.DROUGHT,
        region="Sertão PE",
        latitude=-8.0,
        longitude=-37.0,
        start_date="2026-01-01",
        end_date="2026-06-30",
        trigger_value=200.0,  # 200mm precipitation
        trigger_condition="below",  # Payout if < 200mm
        payout_amount=50000,  # R$ 50,000
        currency="BRL",
        oracle_source="INMET",
    )
    
    # Create token
    token = token_service.create_climate_token(
        name="ClimateWise Drought Index Sertão 2026",
        symbol="CLMT-DROUGHT-PE-2026",
        total_supply=10000,
        metadata=metadata,
    )
    
    print(f"\n✅ Token criado com sucesso!")
    print(f"   Token UID: {token.token_uid}")
    print(f"   Nome: {token.name}")
    print(f"   Símbolo: {token.symbol}")
    print(f"   Supply: {token.total_supply:,}")
    print(f"   Região: {token.metadata.region}")
    print(f"   Trigger: {token.metadata.trigger_value}mm {token.metadata.trigger_condition}")
    print(f"   Payout: R$ {token.metadata.payout_amount / 1000:.2f}")
    print(f"   Explorer: {token.token_uid}")  # In production, real URL
    
    return token


def demo_flood_token():
    """Demonstrate flood token creation"""
    print_header("3. CRIAÇÃO DE TOKEN DE ENCHENTE")
    
    token_service = get_climate_token_service()
    
    # Create flood token using convenience method
    print("📝 Criando token de enchente (Flood Index)...")
    token = token_service.create_flood_token(
        region="Petrópolis RJ",
        latitude=-22.5051,
        longitude=-43.1783,
        start_date="2026-01-01",
        end_date="2026-03-31",
        trigger_precipitation_mm=300.0,
        payout_amount=100000,
        total_supply=10000,
    )
    
    print(f"\n✅ Token de enchente criado!")
    print(f"   Token UID: {token.token_uid}")
    print(f"   Símbolo: {token.symbol}")
    print(f"   Trigger: > {token.metadata.trigger_value}mm")
    print(f"   Payout: R$ {token.metadata.payout_amount / 1000:.2f}")
    
    return token


def demo_oracle_query():
    """Demonstrate oracle data query"""
    print_header("4. CONSULTA DE DADOS CLIMÁTICOS (ORACLE)")
    
    oracle = get_climate_oracle_service()
    
    print("🌡️  Buscando dados históricos de precipitação...")
    print(f"   Localização: São Paulo (-23.5505, -46.6333)")
    print(f"   Período: Últimos 30 dias")
    
    # Get historical data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        data_points = oracle.get_historical_data(
            latitude=-23.5505,
            longitude=-46.6333,
            start_date=start_date,
            end_date=end_date,
            source="openmeteo",
        )
        
        print(f"\n✅ Dados obtidos com sucesso!")
        print(f"   Pontos de dados: {len(data_points)}")
        print(f"   Fonte: {data_points[0].source if data_points else 'N/A'}")
        
        # Calculate precipitation sum
        total_precip = oracle.calculate_precipitation_index(data_points, "sum")
        avg_temp = oracle.calculate_temperature_index(data_points, "avg")
        
        print(f"\n📊 Índices calculados:")
        print(f"   Precipitação total (30 dias): {total_precip:.1f}mm")
        print(f"   Temperatura média: {avg_temp:.1f}°C")
        
        # Check trigger example
        print(f"\n🎯 Exemplo de trigger:")
        print(f"   Se trigger = 150mm (below)")
        trigger_met = oracle.check_trigger(total_precip, 150.0, "below")
        print(f"   Valor atual: {total_precip:.1f}mm")
        print(f"   Trigger atingido: {'✅ SIM' if trigger_met else '❌ NÃO'}")
        
    except Exception as e:
        print(f"\n⚠️  Erro ao buscar dados: {str(e)}")
        print("   (Em produção, integrar com API OpenMeteo/INMET)")


def demo_payout_execution():
    """Demonstrate automatic payout execution"""
    print_header("5. EXECUÇÃO AUTOMÁTICA DE PAYOUT")
    
    token_service = get_climate_token_service()
    
    # Get first token
    tokens = token_service.list_tokens()
    if not tokens:
        print("❌ Nenhum token encontrado")
        return
    
    token = tokens[0]
    
    print(f"📋 Token: {token.symbol}")
    print(f"   Condição: {token.metadata.trigger_condition} {token.metadata.trigger_value}mm")
    print(f"   Payout: R$ {token.metadata.payout_amount / 1000:.2f}")
    
    # Simulate oracle value
    print(f"\n🔍 Verificando condição de payout...")
    
    # Example: precipitation was 150mm (below 200mm trigger)
    simulated_oracle_value = 150.0
    
    print(f"   Valor do oracle: {simulated_oracle_value}mm")
    print(f"   Trigger: {token.metadata.trigger_value}mm {token.metadata.trigger_condition}")
    
    trigger_met = oracle_service.check_trigger(
        simulated_oracle_value,
        token.metadata.trigger_value,
        token.metadata.trigger_condition,
    )
    
    print(f"\n   Trigger atingido: {'✅ SIM' if trigger_met else '❌ NÃO'}")
    
    if trigger_met:
        print(f"\n💰 Executando payout automático...")
        print(f"   Beneficiário: farmer_wallet_address")
        print(f"   Valor: R$ {token.metadata.payout_amount / 1000:.2f}")
        
        # In production, execute real payout:
        # result = token_service.execute_payout(
        #     token_uid=token.token_uid,
        #     oracle_value=simulated_oracle_value,
        #     beneficiary_address="farmer_wallet",
        # )
        
        print(f"\n✅ Payout executado com sucesso! (mock)")
        print(f"   Status do token: PAID_OUT")
    else:
        print(f"\nℹ️  Payout não executado (condição não atingida)")


def demo_token_list():
    """List all created tokens"""
    print_header("6. LISTA DE TOKENS CRIADOS")
    
    token_service = get_climate_token_service()
    tokens = token_service.list_tokens()
    
    if not tokens:
        print("❌ Nenhum token criado")
        return
    
    print(f"📊 Total de tokens: {len(tokens)}\n")
    
    for i, token in enumerate(tokens, 1):
        print(f"{i}. {token.symbol}")
        print(f"   UID: {token.token_uid}")
        print(f"   Tipo: {token.metadata.index_type.value}")
        print(f"   Região: {token.metadata.region}")
        print(f"   Status: {token.status.value}")
        print(f"   Payout Executado: {'✅ Sim' if token.payout_executed else '❌ Não'}")
        print()


def main():
    """Main demonstration function"""
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  HATHOR BLOCKCHAIN DEMO".center(78) + "█")
    print("█" + "  Tokenização de Índices Climáticos".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    # Run demonstrations
    demo_hathor_initialization()
    demo_token_creation()
    demo_flood_token()
    demo_oracle_query()
    demo_payout_execution()
    demo_token_list()
    
    # Final summary
    print_header("RESUMO DA DEMONSTRAÇÃO")
    
    print("✅ FUNCIONALIDADES DEMONSTRADAS:")
    print()
    print("   1. ✅ Inicialização da Hathor Blockchain")
    print("   2. ✅ Criação de Token de Seca (Drought)")
    print("   3. ✅ Criação de Token de Enchente (Flood)")
    print("   4. ✅ Consulta de Dados Climáticos (Oracle)")
    print("   5. ✅ Execução Automática de Payout")
    print("   6. ✅ Listagem de Tokens")
    print()
    
    print("📁 ARQUIVOS CRIADOS:")
    print()
    print("   ✅ blockchain/hathor/config.py")
    print("   ✅ blockchain/hathor/hathor_service.py")
    print("   ✅ blockchain/hathor/climate_token_service.py")
    print("   ✅ blockchain/hathor/oracle_service.py")
    print("   ✅ api/hathor_blockchain.py")
    print("   ✅ requirements-blockchain.txt")
    print()
    
    print("🚀 PRÓXIMOS PASSOS:")
    print()
    print("   1. Integrar com hathor-wallet-lib para operações reais")
    print("   2. Configurar API keys (OpenMeteo, INMET)")
    print("   3. Testar em testnet da Hathor")
    print("   4. Implementar Nano Contracts avançados")
    print("   5. Deploy em produção (mainnet)")
    print()
    
    print("█" * 80)
    print("█" + "  DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO".center(78) + "█")
    print("█" + "  Modo: DESENVOLVIMENTO (Mock)".center(78) + "█")
    print("█" + "  Para produção: integrar com wallet library".center(78) + "█")
    print("█" * 80 + "\n")


if __name__ == "__main__":
    # Initialize oracle service for demo
    from blockchain.hathor.oracle_service import get_climate_oracle_service
    oracle_service = get_climate_oracle_service()
    
    main()
