"""
Teste dos endpoints da API de blockchain tokens
"""

import json
from datetime import datetime, timedelta

import requests

BASE_URL = "http://localhost:8000"


def testar_endpoints_blockchain():
    """Testa todos os endpoints de blockchain tokens"""

    print("🔗 Testando Endpoints da API de Blockchain Tokens")
    print("=" * 60)

    # 1. Testar endpoint de saúde
    print("🏥 Testando endpoint de saúde...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Servidor está saudável!")
        else:
            print(f"❌ Servidor respondeu com status {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Erro ao conectar com servidor: {e}")
        return
    print()

    # 2. Testar criação de token blockchain
    print("🏭 Testando criação de token blockchain...")

    # Primeiro, criar um evento climático via API
    evento_data = {
        "tipo": "enchente",
        "latitude": -8.7618,
        "longitude": -63.9039,
        "data_inicio": (datetime.now() - timedelta(days=2)).isoformat(),
        "data_fim": (datetime.now() - timedelta(days=1)).isoformat(),
        "intensidade": 4.5,
        "probabilidade": 0.88,
        "descricao": "Enchente severa no Rio Madeira - Porto Velho",
        "nivel_alerta": 5,
    }

    try:
        response = requests.post(f"{BASE_URL}/eventos", json=evento_data)
        if response.status_code == 200:
            evento_criado = response.json()
            evento_id = evento_criado["id"]
            print(f"✅ Evento climático criado com ID: {evento_id}")
        else:
            print(f"❌ Erro ao criar evento: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return
    print()

    # 3. Testar mint de token blockchain
    print("🪙 Testando mint de token blockchain...")

    mint_data = {
        "evento_id": evento_id,
        "wallet_address": "climateai_wallet_test_api_001",
        "token_supply": 1000000,
        "decimals": 0,
        "metadata": {
            "region": "Porto Velho, Rondônia",
            "impact_area": "Rio Madeira Basin",
            "affected_population": 500000,
            "economic_impact": "high",
            "mitigation_required": True,
        },
    }

    try:
        response = requests.post(f"{BASE_URL}/blockchain/mint", json=mint_data)
        if response.status_code == 200:
            mint_result = response.json()
            token_uid = mint_result["token_uid"]
            tx_id = mint_result["transaction_id"]
            print("✅ Token blockchain criado via API!")
            print(f"  Transaction ID: {tx_id}")
            print(f"  Token UID: {token_uid}")
            print(f"  Climate Token ID: {mint_result['climate_token_id']}")
            print(
                f"  Token Symbol: {mint_result['blockchain_token']['token_data']['symbol']}"
            )
        else:
            print(f"❌ Erro no mint: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return
    print()

    # 4. Testar busca de informações do token
    print("🔍 Testando busca de informações do token...")

    try:
        response = requests.get(f"{BASE_URL}/blockchain/token/{token_uid}")
        if response.status_code == 200:
            token_info = response.json()
            print("✅ Informações do token obtidas!")
            print(f"  Proprietário: {token_info['owner_address']}")
            print(f"  Supply inicial: {token_info['initial_supply']:,}")
            climate_event = token_info["token_data"]["climate_event"]
            print(
                f"  Evento: {climate_event['event_type']} (Severidade: {climate_event['severity_level']})"
            )
        else:
            print(f"❌ Erro ao buscar token: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    print()

    # 5. Testar busca de transação
    print("📄 Testando busca de informações da transação...")

    try:
        response = requests.get(f"{BASE_URL}/blockchain/transaction/{tx_id}")
        if response.status_code == 200:
            tx_info = response.json()
            print("✅ Informações da transação obtidas!")
            print(f"  Tipo: {tx_info['type']}")
            print(f"  Status: {tx_info['status']}")
            print(f"  Timestamp: {tx_info['timestamp']}")
        else:
            print(
                f"❌ Erro ao buscar transação: {response.status_code} - {response.text}"
            )
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    print()

    # 6. Testar transferência de tokens
    print("💸 Testando transferência de tokens...")

    transfer_data = {
        "token_uid": token_uid,
        "from_address": "climateai_wallet_test_api_001",
        "to_address": "climateai_wallet_recipient_api_001",
        "amount": 50000,
    }

    try:
        response = requests.post(f"{BASE_URL}/blockchain/transfer", json=transfer_data)
        if response.status_code == 200:
            transfer_result = response.json()
            print("✅ Transferência realizada via API!")
            print(f"  Transaction ID: {transfer_result['transaction_id']}")
            print(f"  Valor transferido: 50,000 tokens")
        else:
            print(f"❌ Erro na transferência: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    print()

    # 7. Testar listagem de tokens por proprietário
    print("📋 Testando listagem de tokens por proprietário...")

    try:
        response = requests.get(
            f"{BASE_URL}/blockchain/tokens/owner/climateai_wallet_recipient_api_001"
        )
        if response.status_code == 200:
            owner_tokens = response.json()
            print(f"✅ Tokens do destinatário: {len(owner_tokens)}")
            for token in owner_tokens:
                print(
                    f"    - {token['token_data']['symbol']}: {token['token_data']['name']}"
                )
        else:
            print(f"❌ Erro ao listar tokens: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    print()

    # 8. Testar busca por tipo de evento
    print("🌍 Testando busca por tipo de evento...")

    try:
        response = requests.get(f"{BASE_URL}/blockchain/tokens/event-type/enchente")
        if response.status_code == 200:
            enchente_tokens = response.json()
            print(f"✅ Tokens de enchente encontrados: {len(enchente_tokens)}")
        else:
            print(
                f"❌ Erro ao buscar por tipo: {response.status_code} - {response.text}"
            )
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    print()

    # 9. Testar estatísticas da blockchain
    print("📊 Testando estatísticas da blockchain...")

    try:
        response = requests.get(f"{BASE_URL}/blockchain/stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Estatísticas obtidas!")
            print(f"  Total de registros: {stats['total_registros']}")
            print(f"  Transações: {stats['transacoes']}")
            print(f"  Tokens: {stats['tokens']}")
            print(f"  Rede: {stats['rede']}")
        else:
            print(
                f"❌ Erro ao obter estatísticas: {response.status_code} - {response.text}"
            )
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    print()

    print("🎉 Todos os testes de endpoints da API foram concluídos!")


if __name__ == "__main__":
    testar_endpoints_blockchain()
