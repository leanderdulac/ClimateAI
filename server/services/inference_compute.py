"""Remote DePIN / Akash inference probe. Never log or return the service URL."""

from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

HEALTH_TIMEOUT_SECONDS = 2.5
CACHE_TTL_SECONDS = 45.0
ALLOWED_SCHEMES = frozenset({"http", "https"})

_cache: Optional[dict[str, Any]] = None
_cache_monotonic: float = 0.0
_lock = asyncio.Lock()


def reset_inference_compute_cache() -> None:
    global _cache, _cache_monotonic
    _cache = None
    _cache_monotonic = 0.0


def inference_service_url() -> Optional[str]:
    raw = (os.getenv("INFERENCE_SERVICE_URL") or "").strip()
    if not raw:
        return None
    parsed = urlparse(raw)
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.hostname:
        return None
    return raw.rstrip("/")


def inference_auth_headers() -> dict[str, str]:
    """Optional Bearer token for remote /health and /predict."""
    token = (os.getenv("INFERENCE_SERVICE_TOKEN") or "").strip()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def inference_endpoint(path: str) -> Optional[str]:
    base = inference_service_url()
    if not base:
        return None
    return f"{base}/{path.lstrip('/')}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _payload(
    status: str,
    mode: str,
    latency_ms: Optional[int],
    last_checked: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "mode": mode,
        "latency_ms": latency_ms,
        "last_checked": last_checked or _utc_now(),
    }


async def request_inference(
    method: str,
    path: str,
    *,
    timeout: float = HEALTH_TIMEOUT_SECONDS,
    json: Any = None,
    client: Optional[httpx.AsyncClient] = None,
) -> httpx.Response:
    """Call a path on the configured inference host with optional Bearer token."""
    url = inference_endpoint(path)
    if not url:
        raise RuntimeError("inference service is not configured")
    headers = inference_auth_headers()
    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=timeout),
            follow_redirects=False,
        )
    try:
        return await client.request(method.upper(), url, headers=headers, json=json)
    finally:
        if owns_client:
            await client.aclose()


async def probe_inference_health(
    *,
    force: bool = False,
    client: Optional[httpx.AsyncClient] = None,
) -> dict[str, Any]:
    global _cache, _cache_monotonic
    async with _lock:
        now = time.monotonic()
        if (
            not force
            and _cache is not None
            and (now - _cache_monotonic) < CACHE_TTL_SECONDS
        ):
            return dict(_cache)

        if inference_service_url() is None:
            result = _payload("not_configured", "local", None)
            _cache = result
            _cache_monotonic = now
            return dict(result)

        started = time.perf_counter()
        try:
            response = await request_inference(
                "GET",
                "/health",
                timeout=HEALTH_TIMEOUT_SECONDS,
                client=client,
            )
            latency_ms = max(0, int(round((time.perf_counter() - started) * 1000)))
            if 200 <= response.status_code < 400:
                result = _payload("online", "remote", latency_ms)
            else:
                result = _payload("offline", "local_fallback", latency_ms)
        except (httpx.HTTPError, OSError, RuntimeError):
            latency_ms = max(0, int(round((time.perf_counter() - started) * 1000)))
            result = _payload("offline", "local_fallback", latency_ms)

        _cache = result
        _cache_monotonic = time.monotonic()
        return dict(result)
