"""GET /api/v1/blockchain/base/status — Base L2 probe without chain env."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_base_status_not_configured_without_rpc(
    authenticated_client: TestClient, monkeypatch
):
    monkeypatch.delenv("BASE_RPC_URL", raising=False)
    monkeypatch.delenv("BASE_CHAIN_ID", raising=False)
    monkeypatch.delenv("BASE_CONTRACT_ADDRESS", raising=False)
    monkeypatch.delenv("CLIMATE_POLICY_CONTRACT", raising=False)

    response = authenticated_client.get("/api/v1/blockchain/base/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_configured"
    assert body["network"] == "base"
    assert body["latest_block"] is None


@pytest.mark.unit
def test_base_status_online_when_rpc_responds(
    authenticated_client: TestClient, monkeypatch
):
    monkeypatch.setenv("BASE_RPC_URL", "https://example.invalid")
    monkeypatch.setenv("BASE_CHAIN_ID", "84532")
    monkeypatch.setenv("BASE_CONTRACT_ADDRESS", "0xabc")

    async def fake_rpc(_url: str, method: str):
        if method == "eth_chainId":
            return "0x14a34"
        if method == "eth_blockNumber":
            return "0x10"
        raise AssertionError(method)

    monkeypatch.setattr("services.base_status._rpc", fake_rpc)

    response = authenticated_client.get("/api/v1/blockchain/base/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "online"
    assert body["chain_id"] == 84532
    assert body["latest_block"] == 16
    assert body["contracts"]["policy"] == "0xabc"


@pytest.mark.unit
def test_base_status_requires_auth(client: TestClient):
    response = client.get("/api/v1/blockchain/base/status")
    assert response.status_code == 401


@pytest.mark.unit
def test_app_imports_without_base_env(monkeypatch):
    monkeypatch.delenv("BASE_RPC_URL", raising=False)
    from blockchain.base.config import get_base_config

    assert get_base_config().configured is False
