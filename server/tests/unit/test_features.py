"""Product feature flags and path gating."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from lib.features import current_flags, disabled_feature_for_path


@pytest.mark.unit
def test_features_endpoint_is_public(client: TestClient):
    response = client.get("/api/v1/features")
    assert response.status_code == 200
    payload = response.json()
    assert payload["atlas"] is True
    assert payload["blockchain"] is True
    assert payload["assistant"] is True


@pytest.mark.unit
def test_disabled_feature_for_path_when_flags_on():
    assert disabled_feature_for_path("/api/v1/gemini/chat") is None
    assert disabled_feature_for_path("/api/v1/blockchain/hathor/status") is None
    assert disabled_feature_for_path("/api/v1/atlas-realtime/risk-summary") is None


@pytest.mark.unit
def test_disabled_feature_for_path_when_assistant_off():
    with patch("lib.features.current_flags", return_value={"atlas": True, "blockchain": True, "assistant": False}):
        assert disabled_feature_for_path("/api/v1/gemini/chat") == "assistant"
        assert disabled_feature_for_path("/api/v1/grok/analyze") == "assistant"
        assert disabled_feature_for_path("/api/v1/pricing/quote") is None


@pytest.mark.unit
def test_disabled_atlas_returns_404(client: TestClient, monkeypatch):
    monkeypatch.setattr("lib.features.settings.FEATURE_ATLAS", False)
    response = client.get("/api/v1/atlas-realtime/risk-summary")
    assert response.status_code == 404
    assert "atlas" in response.json()["detail"]
