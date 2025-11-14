"""
Teste da funcionalidade de tokens blockchain para eventos climáticos
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from models.schemas import EventoClimatico, EventoClimaticoTipo
from services.blockchain_token_service import BlockchainTokenService

def testar_blockchain_tokens():
    """Testa a funcionalidade completa de tokens blockchain"""

    print("🔗 Testando Tokens Blockchain para Eventos Climáticos")
    print("=" * 60)

    # Inicializar serviço
    blockchain_service = BlockchainTokenService()

    # Criar evento climático de teste
    evento_teste = EventoClimatico(
        tipo=EventoClimaticoTipo.ENCHENTE,
        latitude=-8.7618,
        longitude=-63.9039,
        data_inicio=datetime.now() - timedelta(days=2),
        data_fim=datetime.now() - timedelta(days=1),
        intensidade=4.5,
        probabilidade=0.88,
        descricao="Enchente severa no Rio Madeira - Porto Velho",
        nivel_alerta=5
    )

    print("🌊 Evento de teste:")
    print(f"  Tipo: {evento_teste.tipo.value}")
    print(f"  Localização: Porto Velho, RO")
    print(f"  Intensidade: {evento_teste.intensidade}")
    print(f"  Probabilidade: {evento_teste.probabilidade}")
    print()

    # Testar criação de token
    print("🏭 Criando token blockchain...")
    wallet_address = "climateai_wallet_test_001"

    resultado_mint = blockchain_service.mint_climate_token(
        evento=evento_teste,
        wallet_address=wallet_address,
        token_supply=1000000,  # 1M tokens
        decimals=0,
        metadata={
            "region": "Porto Velho, Rondônia",
            "impact_area": "Rio Madeira Basin",
            "affected_population": 500000,
            "economic_impact": "high",
            "mitigation_required": True
        }
    )

    if resultado_mint["success"]:
        token_uid = resultado_mint["token_uid"]
        tx_id = resultado_mint["transaction_id"]

        print("✅ Token blockchain criado com sucesso!")
        print(f"  Transaction ID: {tx_id}")
        print(f"  Token UID: {token_uid}")
        print(f"  Climate Token ID: {resultado_mint['climate_token_id']}")
        print(f"  Token Symbol: {resultado_mint['blockchain_token']['token_data']['symbol']}")
        print(f"  Token Name: {resultado_mint['blockchain_token']['token_data']['name']}")
        print(f"  Supply: {resultado_mint['blockchain_token']['initial_supply']:,} tokens")
        print()

        # Testar busca de token
        print("🔍 Buscando informações do token...")
        token_info = blockchain_service.get_token_info(token_uid)
        if token_info:
            print("✅ Token encontrado!")
            print(f"  Proprietário: {token_info['owner_address']}")
            print(f"  Supply inicial: {token_info['initial_supply']:,}")
            climate_event = token_info['token_data']['climate_event']
            print(f"  Evento climático: {climate_event['event_type']} (Severidade: {climate_event['severity_level']})")
            print(f"  Localização: {climate_event['latitude']}, {climate_event['longitude']}")
        print()

        # Testar busca de transação
        print("📄 Buscando informações da transação...")
        tx_info = blockchain_service.get_transaction_info(tx_id)
        if tx_info:
            print("✅ Transação encontrada!")
            print(f"  Tipo: {tx_info['type']}")
            print(f"  Status: {tx_info['status']}")
            print(f"  Timestamp: {tx_info['timestamp']}")
            print(f"  Outputs: {len(tx_info['outputs'])}")
        print()

        # Testar transferência
        print("💸 Testando transferência de tokens...")
        recipient_address = "climateai_wallet_recipient_001"

        transfer_result = blockchain_service.transfer_token(
            token_uid=token_uid,
            from_address=wallet_address,
            to_address=recipient_address,
            amount=50000  # 50k tokens
        )

        if transfer_result["success"]:
            print("✅ Transferência realizada com sucesso!")
            print(f"  Transaction ID: {transfer_result['transaction_id']}")
            print(f"  Valor transferido: 50,000 tokens")
            print(f"  Destinatário: {recipient_address}")
        else:
            print(f"❌ Erro na transferência: {transfer_result['error']}")
        print()

        # Verificar mudança de proprietário
        print("🔄 Verificando mudança de proprietário...")
        updated_token = blockchain_service.get_token_info(token_uid)
        if updated_token:
            print(f"  Novo proprietário: {updated_token['owner_address']}")
        print()

    else:
        print(f"❌ Erro ao criar token: {resultado_mint['error']}")
        return

    # Testar listagem de tokens por proprietário
    print("📋 Listando tokens do proprietário original...")
    owner_tokens = blockchain_service.list_tokens_by_owner(wallet_address)
    print(f"  Tokens encontrados: {len(owner_tokens)}")
    for token in owner_tokens:
        print(f"    - {token['token_data']['symbol']}: {token['token_data']['name']}")
    print()

    print("📋 Listando tokens do destinatário...")
    recipient_tokens = blockchain_service.list_tokens_by_owner(recipient_address)
    print(f"  Tokens encontrados: {len(recipient_tokens)}")
    for token in recipient_tokens:
        print(f"    - {token['token_data']['symbol']}: {token['token_data']['name']}")
    print()

    # Testar busca por tipo de evento
    print("🌍 Buscando tokens por tipo de evento...")
    enchente_tokens = blockchain_service.get_climate_event_tokens(EventoClimaticoTipo.ENCHENTE)
    print(f"  Tokens de enchente: {len(enchente_tokens)}")

    seca_tokens = blockchain_service.get_climate_event_tokens(EventoClimaticoTipo.SECA)
    print(f"  Tokens de seca: {len(seca_tokens)}")

    todos_tokens = blockchain_service.get_climate_event_tokens()
    print(f"  Todos os tokens climáticos: {len(todos_tokens)}")
    print()

    # Estatísticas da blockchain
    print("📊 Estatísticas da blockchain ClimateAI:")
    stats = blockchain_service.blockchain_registry
    transactions = [item for item in stats.values() if isinstance(item, dict) and 'tx_id' in item]
    tokens = [item for item in stats.values() if isinstance(item, dict) and 'token_uid' in item]

    print(f"  Total de registros: {len(stats)}")
    print(f"  Transações: {len(transactions)}")
    print(f"  Tokens: {len(tokens)}")
    print(f"  Rede: {blockchain_service.network}")
    print()

    print("🎉 Todos os testes de tokens blockchain foram concluídos!")

if __name__ == "__main__":
    testar_blockchain_tokens()