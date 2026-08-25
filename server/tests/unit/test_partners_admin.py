"""Admin partner + API key issuance."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_partners_require_auth(client: TestClient):
    response = client.get("/api/v1/partners")
    assert response.status_code == 401


@pytest.mark.unit
def test_create_partner_generate_and_revoke_key(authenticated_client: TestClient):
    created = authenticated_client.post(
        "/api/v1/partners",
        json={"name": "Cooperativa Vale", "slug": "coop-vale", "contact_email": "ops@vale.test"},
    )
    assert created.status_code == 201, created.text
    partner = created.json()
    assert partner["slug"] == "coop-vale"
    assert partner["api_enabled"] is True

    listed = authenticated_client.get("/api/v1/partners")
    assert listed.status_code == 200
    assert any(item["id"] == partner["id"] for item in listed.json())

    issued = authenticated_client.post(
        f"/api/v1/partners/{partner['id']}/api-keys",
        json={"name": "Backend produção"},
    )
    assert issued.status_code == 201, issued.text
    body = issued.json()
    assert body["secret_key"].startswith("sk_live_")
    assert body["prefix"].startswith("sk_live_")
    assert body["is_active"] is True
    key_id = body["id"]

    keys = authenticated_client.get(f"/api/v1/partners/{partner['id']}/api-keys")
    assert keys.status_code == 200
    assert any(item["id"] == key_id for item in keys.json())

    revoked = authenticated_client.delete(f"/api/v1/partners/{partner['id']}/api-keys/{key_id}")
    assert revoked.status_code == 200

    keys_after = authenticated_client.get(f"/api/v1/partners/{partner['id']}/api-keys")
    match = next(item for item in keys_after.json() if item["id"] == key_id)
    assert match["is_active"] is False


@pytest.mark.unit
def test_partner_slug_is_normalized(authenticated_client: TestClient):
    response = authenticated_client.post(
        "/api/v1/partners",
        json={"name": "Acme Coop", "slug": "Acme Coop"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["slug"] == "acme-coop"
