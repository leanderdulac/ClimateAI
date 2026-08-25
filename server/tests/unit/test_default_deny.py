"""Default-deny authentication middleware."""

import pytest
from fastapi.testclient import TestClient

from middleware.auth_middleware import is_public_path


def test_public_paths_allowlist():
    assert is_public_path("/health", "GET") is True
    assert is_public_path("/", "GET") is True
    assert is_public_path("/api/v1/auth/login", "POST") is True
    assert is_public_path("/api/v1/auth/register", "POST") is True
    assert is_public_path("/api/v1/auth/refresh", "POST") is True
    assert is_public_path("/api/v1/auth/forgot-password", "POST") is True
    assert is_public_path("/api/v1/features", "GET") is True
    assert is_public_path("/api/v1/pricing/calculate", "POST") is False
    assert is_public_path("/api/v1/health/full", "GET") is False
    assert is_public_path("/api/v1/blockchain/hathor/status", "GET") is False
    assert is_public_path("/docs", "GET", environment="development") is True
    assert is_public_path("/docs", "GET", environment="production") is False
    assert is_public_path("/anything", "OPTIONS") is True


@pytest.mark.unit
def test_health_remains_public(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200


@pytest.mark.unit
def test_features_endpoint_is_public(client: TestClient):
    response = client.get("/api/v1/features")
    assert response.status_code == 200


@pytest.mark.unit
def test_root_remains_public(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.unit
def test_protected_pricing_returns_401_without_token(client: TestClient):
    response = client.post("/api/v1/policy-pricing/calculate", json={})
    assert response.status_code == 401


@pytest.mark.unit
def test_protected_hathor_returns_401_without_token(client: TestClient):
    response = client.get("/api/v1/blockchain/hathor/status")
    assert response.status_code == 401


@pytest.mark.unit
def test_health_full_requires_auth(client: TestClient):
    response = client.get("/api/v1/health/full")
    assert response.status_code == 401


@pytest.mark.unit
def test_mlflow_transition_requires_auth(client: TestClient):
    response = client.post("/api/v1/mlflow/models/demo/transition?version=1&stage=Production")
    assert response.status_code == 401


@pytest.mark.unit
def test_invalid_bearer_token_is_rejected(client: TestClient):
    response = client.get(
        "/api/v1/blockchain/hathor/status",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


@pytest.mark.unit
def test_authenticated_request_is_not_blocked_by_default_deny(authenticated_client: TestClient):
    response = authenticated_client.get("/api/v1/auth/me")
    assert response.status_code != 401
