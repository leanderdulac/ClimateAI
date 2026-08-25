"""Contract tests: unauthenticated callers receive 401 on protected product APIs."""

import pytest
from fastapi.testclient import TestClient

PROTECTED_POSTS = (
    "/api/v1/pricing/quote",
    "/api/v1/pricing/calculate",
    "/api/v1/policy-pricing/calculate",
    "/api/v1/blockchain/hathor/tokens/create",
    "/api/v1/gemini/chat",
    "/api/v1/grok/analyze",
    "/api/v1/mlflow/models/demo/transition",
)

PROTECTED_GETS = (
    "/api/v1/blockchain/hathor/status",
    "/api/v1/gemini/capabilities",
    "/api/v1/grok/status",
    "/api/v1/partners",
)


@pytest.mark.unit
@pytest.mark.parametrize("path", PROTECTED_POSTS)
def test_protected_post_returns_401_without_token(client: TestClient, path: str):
    response = client.post(path, json={})
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.unit
@pytest.mark.parametrize("path", PROTECTED_GETS)
def test_protected_get_returns_401_without_token(client: TestClient, path: str):
    response = client.get(path)
    assert response.status_code == 401
    assert "detail" in response.json()
