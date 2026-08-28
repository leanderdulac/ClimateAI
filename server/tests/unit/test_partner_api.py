"""Partner integration API contract."""

import pytest
from fastapi.testclient import TestClient

from middleware.auth_middleware import is_public_path

PARTNER_KEY = {"X-API-Key": "cw_dev_partner_key"}


@pytest.mark.unit
def test_partner_catalog_is_public(client: TestClient):
    assert is_public_path("/api/v1/partner/catalog", "GET") is True
    response = client.get("/api/v1/partner/catalog")
    assert response.status_code == 200
    body = response.json()
    assert body["base_url"].endswith("/partner")
    assert body["authentication"]["name"] == "X-API-Key"
    assert "xyz_tiles" in body["geo"]
    assert "wmts" in body["geo"]
    assert body["geo"]["feature_format"].startswith("GeoJSON")
    assert "open-meteo" in body["licenses"]
    assert body["rate_limits"]["requests_per_minute"] == 60
    paths = {item["path"] for item in body["endpoints"]}
    assert "/climate/current" in paths
    assert "/pricing/quote" in paths
    assert "/pricing/simulate" in paths
    assert "/agri/plan" in paths
    assert "/geo/layers" in paths


@pytest.mark.unit
def test_partner_climate_requires_api_key(client: TestClient):
    response = client.get("/api/v1/partner/climate/current", params={"lat": -23.55, "lon": -46.63})
    assert response.status_code == 401


@pytest.mark.unit
def test_partner_climate_current_envelope(client: TestClient):
    response = client.get(
        "/api/v1/partner/climate/current",
        params={"lat": -23.55, "lon": -46.63},
        headers=PARTNER_KEY,
    )
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert "meta" in body
    assert body["meta"]["status"] in {"fresh", "stale", "unavailable"}
    assert "stale" in body["meta"]
    assert "updated_at" in body["meta"]
    assert "source" in body["meta"]
    assert "license" in body["meta"]
    assert "attribution" in body["meta"]["license"]


@pytest.mark.unit
def test_partner_geo_layers_formats(client: TestClient):
    response = client.get("/api/v1/partner/geo/layers", headers=PARTNER_KEY)
    assert response.status_code == 200
    layers = response.json()["data"]
    assert layers["xyz"]
    assert layers["wmts"]
    assert "GeoJSON" in layers["geojson"] or "geojson" in layers["geojson"].lower()


@pytest.mark.unit
def test_partner_geo_feature_is_geojson(client: TestClient):
    response = client.get(
        "/api/v1/partner/geo/feature",
        params={"lat": -15.78, "lon": -47.93},
        headers=PARTNER_KEY,
    )
    assert response.status_code == 200
    feature = response.json()["data"]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    assert feature["geometry"]["coordinates"] == [-47.93, -15.78]


@pytest.mark.unit
def test_partner_agri_catalog(client: TestClient):
    response = client.get("/api/v1/partner/agri/catalog", headers=PARTNER_KEY)
    assert response.status_code == 200
    assert response.json()["meta"]["status"] in {"fresh", "stale", "unavailable"}
