"""Canonical pricing quote and deprecation headers."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_pricing_quote_requires_auth(client: TestClient):
    response = client.post("/api/v1/pricing/quote", json={"asset_value": 100000})
    assert response.status_code == 401


@pytest.mark.unit
def test_legacy_policy_pricing_is_deprecated(client: TestClient):
    response = client.post(
        "/api/v1/policy-pricing/calculate",
        json={"asset_value": 100000, "severity_amount": 1000, "frequency_pct": 5},
    )
    assert response.status_code == 401
    assert response.headers.get("deprecation") == "true"
    assert "/api/v1/pricing/quote" in (response.headers.get("link") or "")


@pytest.mark.unit
def test_legacy_unified_pricing_is_deprecated(client: TestClient):
    response = client.post("/api/v1/unified-pricing/calculate", json={})
    assert response.status_code == 401
    assert response.headers.get("deprecation") == "true"
