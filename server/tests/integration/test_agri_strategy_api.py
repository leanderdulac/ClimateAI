import pytest


@pytest.mark.integration
class TestAgriStrategyApi:
    def test_catalog_endpoint(self, client):
        response = client.get("/api/v1/agri-strategy/catalog")
        assert response.status_code == 200
        body = response.json()
        assert "supported_crops" in body
        assert "supported_stages" in body

    def test_plan_endpoint(self, client, monkeypatch):
        from api import agri_strategy

        async def fake_generate_plan(**_kwargs):
            return {
                "crop_type": "soybean",
                "phenological_stage": "flowering",
                "planning_horizon_days": 120,
                "risk_tolerance": "medium",
                "climate_outlook": {"enso": {"regime_label": "el_nino"}, "forecast_source": "NOAA/NWS"},
                "exposure_scores": {
                    "heat": 0.8,
                    "drought": 0.75,
                    "excess_rain": 0.3,
                    "flood": 0.2,
                    "wind": 0.4,
                    "disease": 0.45,
                },
                "operational_actions": [{"category": "water_management", "action": "test"}],
                "financial_actions": [{"type": "parametric_insurance", "strategy": "test"}],
                "alert_triggers": [{"name": "heatwave_alert", "condition": "test"}],
                "supported_crops": ["soybean", "corn"],
                "supported_stages": ["planning", "flowering"],
            }

        monkeypatch.setattr(agri_strategy.agri_strategy_service, "generate_plan", fake_generate_plan)

        payload = {
            "crop_type": "soybean",
            "phenological_stage": "flowering",
            "latitude": -23.55,
            "longitude": -46.63,
            "planning_horizon_days": 120,
            "risk_tolerance": "medium",
            "farm_profile": {
                "irrigation_available": False,
                "drainage_level": "medium",
                "soil_cover_level": "medium",
            },
        }

        response = client.post("/api/v1/agri-strategy/plan", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["crop_type"] == "soybean"
        assert "exposure_scores" in body
        assert "operational_actions" in body

    def test_plan_endpoint_invalid_payload_returns_422(self, client):
        invalid_payload = {
            "crop_type": "soybean",
            "phenological_stage": "flowering",
            "latitude": -123.0,
            "longitude": -46.63,
            "planning_horizon_days": 2,
            "risk_tolerance": "extreme",
        }

        response = client.post("/api/v1/agri-strategy/plan", json=invalid_payload)
        assert response.status_code == 422

        body = response.json()
        assert "detail" in body
