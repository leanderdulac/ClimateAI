"""GET /api/v1/compute/status — remote inference probe without leaking the URL."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient

from services.inference_compute import (
    inference_auth_headers,
    inference_endpoint,
    reset_inference_compute_cache,
)


@pytest.fixture(autouse=True)
def _clean_inference_env(monkeypatch):
    monkeypatch.delenv("INFERENCE_SERVICE_URL", raising=False)
    monkeypatch.delenv("INFERENCE_SERVICE_TOKEN", raising=False)
    reset_inference_compute_cache()
    yield
    reset_inference_compute_cache()


def test_not_configured_when_url_unset(client: TestClient):
    response = client.get("/api/v1/compute/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_configured"
    assert body["mode"] == "local"
    assert body["latency_ms"] is None
    assert body["last_checked"]
    dumped = response.text.lower()
    assert "http" not in dumped
    assert "token" not in dumped
    assert "secret" not in dumped


def test_invalid_url_treated_as_not_configured(client: TestClient, monkeypatch):
    monkeypatch.setenv("INFERENCE_SERVICE_URL", "not-a-url")
    response = client.get("/api/v1/compute/status")
    assert response.json()["status"] == "not_configured"
    assert response.json()["mode"] == "local"


def test_online_probe_measures_latency(client: TestClient, monkeypatch):
    monkeypatch.setenv("INFERENCE_SERVICE_URL", "https://inference.example.invalid")
    monkeypatch.setenv("INFERENCE_SERVICE_TOKEN", "super-secret-token")

    fake_response = MagicMock()
    fake_response.status_code = 200
    request_fn = AsyncMock(return_value=fake_response)
    monkeypatch.setattr("services.inference_compute.request_inference", request_fn)

    response = client.get("/api/v1/compute/status")
    body = response.json()
    assert body["status"] == "online"
    assert body["mode"] == "remote"
    assert isinstance(body["latency_ms"], int)
    assert body["latency_ms"] >= 0
    assert "inference.example" not in response.text
    assert "super-secret-token" not in response.text
    request_fn.assert_awaited()
    called_path = request_fn.await_args.args[1]
    assert called_path == "/health"


def test_offline_when_probe_fails(client: TestClient, monkeypatch):
    monkeypatch.setenv("INFERENCE_SERVICE_URL", "https://inference.example.invalid")

    request_fn = AsyncMock(side_effect=httpx.ConnectError("boom"))
    monkeypatch.setattr("services.inference_compute.request_inference", request_fn)

    response = client.get("/api/v1/compute/status")
    body = response.json()
    assert body["status"] == "offline"
    assert body["mode"] == "local_fallback"
    assert "inference.example" not in response.text


def test_http_error_status_is_offline(client: TestClient, monkeypatch):
    monkeypatch.setenv("INFERENCE_SERVICE_URL", "https://inference.example.invalid")
    fake_response = MagicMock()
    fake_response.status_code = 503
    monkeypatch.setattr(
        "services.inference_compute.request_inference",
        AsyncMock(return_value=fake_response),
    )
    body = client.get("/api/v1/compute/status").json()
    assert body["status"] == "offline"
    assert body["mode"] == "local_fallback"


def test_cache_avoids_second_probe(client: TestClient, monkeypatch):
    monkeypatch.setenv("INFERENCE_SERVICE_URL", "https://inference.example.invalid")
    fake_response = MagicMock()
    fake_response.status_code = 200
    request_fn = AsyncMock(return_value=fake_response)
    monkeypatch.setattr("services.inference_compute.request_inference", request_fn)

    first = client.get("/api/v1/compute/status").json()
    second = client.get("/api/v1/compute/status").json()
    assert first["last_checked"] == second["last_checked"]
    assert request_fn.await_count == 1


def test_auth_headers_and_endpoints():
    assert inference_auth_headers() == {}
    assert inference_endpoint("/predict") is None


def test_auth_headers_include_bearer(monkeypatch):
    monkeypatch.setenv("INFERENCE_SERVICE_URL", "https://inference.example.invalid/v1")
    monkeypatch.setenv("INFERENCE_SERVICE_TOKEN", "abc123")
    assert inference_auth_headers() == {"Authorization": "Bearer abc123"}
    assert inference_endpoint("/predict") == "https://inference.example.invalid/v1/predict"
    assert inference_endpoint("/health") == "https://inference.example.invalid/v1/health"


@pytest.mark.asyncio
async def test_request_inference_sends_bearer_on_health_and_predict(monkeypatch):
    monkeypatch.setenv("INFERENCE_SERVICE_URL", "https://inference.example.invalid")
    monkeypatch.setenv("INFERENCE_SERVICE_TOKEN", "abc123")

    seen: list[tuple[str, str, str | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            (
                request.method,
                str(request.url),
                request.headers.get("authorization"),
            )
        )
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, follow_redirects=False) as client:
        from services.inference_compute import request_inference

        health = await request_inference("GET", "/health", client=client)
        predict = await request_inference(
            "POST", "/predict", json={"x": 1}, client=client
        )

    assert health.status_code == 200
    assert predict.status_code == 200
    assert seen[0][0] == "GET"
    assert seen[0][1] == "https://inference.example.invalid/health"
    assert seen[0][2] == "Bearer abc123"
    assert seen[1][0] == "POST"
    assert seen[1][1] == "https://inference.example.invalid/predict"
    assert seen[1][2] == "Bearer abc123"


def test_compute_status_is_public():
    from middleware.auth_middleware import is_public_path

    assert is_public_path("/api/v1/compute/status", "GET") is True
