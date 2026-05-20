from datetime import datetime
from types import SimpleNamespace

import pytest


@pytest.mark.unit
def test_hathor_status_endpoint_returns_integration_details(client, monkeypatch):
    from api import hathor_blockchain

    class FakeHathorService:
        def get_integration_status(self):
            return {
                "mode": "production",
                "network": "testnet",
                "initialized": True,
                "wallet_address": "hth_test_address",
                "rpc_url": "https://node.testnet.hathor.network",
                "full_node_reachable": True,
                "full_node_error": None,
                "headless_wallet_configured": True,
                "headless_wallet_reachable": True,
                "headless_wallet_error": None,
                "production_strict": False,
                "known_tokens": 2,
            }

    monkeypatch.setattr(hathor_blockchain, "get_hathor_service", lambda: FakeHathorService())

    response = client.get("/api/v1/blockchain/hathor/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "production"
    assert payload["headless_wallet_configured"] is True
    assert payload["headless_wallet_reachable"] is True


@pytest.mark.unit
def test_hathor_wallet_balance_endpoint_returns_values(client, monkeypatch):
    from api import hathor_blockchain

    class FakeHathorService:
        def get_balance(self, token_uid: str = "00"):
            return {
                "token_uid": token_uid,
                "available": 120,
                "locked": 5,
                "total": 125,
            }

    monkeypatch.setattr(hathor_blockchain, "get_hathor_service", lambda: FakeHathorService())

    response = client.get("/api/v1/blockchain/hathor/wallet/balance/00")
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_uid"] == "00"
    assert payload["total"] == 125


@pytest.mark.unit
def test_tokenizar_com_mint_returns_on_chain_and_persists_transaction(client, monkeypatch):
    from api import tokenizacao

    class FakeTokenizacaoService:
        async def gerar_token_evento(self, evento):
            return SimpleNamespace(
                token_id="SEC-4-1111-2222-20260519000000",
                event_type=evento.tipo,
                severity_level=4,
                latitude=evento.latitude,
                longitude=evento.longitude,
                start_date=evento.data_inicio,
                end_date=evento.data_fim,
                intensity=evento.intensidade,
                probability=evento.probabilidade,
                location_hash="1111",
                temporal_hash="2222",
                metadata={"on_chain_status": "pending", "tx_hash": None},
                created_at=datetime.now(),
            )

        async def mint_token_on_chain(self, token, destination_address):
            token.metadata["on_chain_status"] = "minted"
            token.metadata["tx_hash"] = "0xabc123"
            return {
                "status": "success",
                "tx_hash": "0xabc123",
                "value": 4000,
                "slot": 77,
                "token_id": token.token_id,
            }

    monkeypatch.setattr(tokenizacao, "token_service", FakeTokenizacaoService())

    payload = {
        "evento": {
            "tipo": "seca",
            "latitude": -15.78,
            "longitude": -47.93,
            "data_inicio": "2026-05-19T00:00:00",
            "data_fim": "2026-05-20T00:00:00",
            "intensidade": 8.2,
            "probabilidade": 72.0,
            "descricao": "Teste de tokenizacao com mint",
            "nivel_alerta": 3,
        },
        "destination_address": "hth_demo_wallet_01",
        "mint_on_chain": True,
    }

    response = client.post("/api/v1/tokenizacao/tokenizar-com-mint", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["on_chain"]["status"] == "success"
    assert body["on_chain"]["tx_hash"] == "0xabc123"


@pytest.mark.unit
def test_tokenizar_com_mint_requires_destination_address(client):
    payload = {
        "evento": {
            "tipo": "seca",
            "latitude": -15.78,
            "longitude": -47.93,
            "data_inicio": "2026-05-19T00:00:00",
            "data_fim": "2026-05-20T00:00:00",
            "intensidade": 8.2,
            "probabilidade": 72.0,
            "descricao": "Teste de validacao",
            "nivel_alerta": 3,
        },
        "mint_on_chain": True,
    }

    response = client.post("/api/v1/tokenizacao/tokenizar-com-mint", json=payload)
    assert response.status_code == 400
    assert "destination_address" in response.json()["detail"]