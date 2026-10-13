"""Unit tests for the MLOps decoupled inference service."""

import pytest
from fastapi.testclient import TestClient
from inference_server import app


@pytest.fixture
def inference_client():
    return TestClient(app)


def test_inference_health(inference_client):
    response = inference_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "device" in data


def test_inference_status(inference_client):
    response = inference_client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "has_torch" in data


def test_inference_predict_endpoint(inference_client, monkeypatch):
    from unittest.mock import MagicMock
    import inference_server

    mock_svc = MagicMock()
    mock_svc.is_trained = True
    mock_svc.predict.return_value = {
        "predictions": [22.4],
        "attention_weights": [[[0.2, 0.2, 0.2, 0.2, 0.2]]],
        "sequence_length_used": 5,
        "model_trained": True,
    }
    monkeypatch.setattr(inference_server, "get_lstm_service", lambda: mock_svc)

    payload = {
        "temperature": [20.0, 21.0, 22.0, 20.5, 21.5, 22.5, 23.0, 22.0, 21.0, 20.0, 21.0, 22.0],
        "precipitation": [5.0, 2.0, 0.0, 1.0, 10.0, 15.0, 2.0, 0.0, 0.0, 4.0, 5.0, 2.0],
        "pressure": [1013.0, 1012.0, 1014.0, 1015.0, 1011.0, 1010.0, 1012.0, 1013.0, 1014.0, 1013.0, 1012.0, 1013.0],
        "nao_index": [0.5, 0.4, 0.6, 0.5, 0.3, 0.2, 0.4, 0.5, 0.6, 0.5, 0.4, 0.5],
        "enso_phase": [0.1, 0.1, 0.2, 0.2, 0.1, 0.0, -0.1, -0.1, 0.0, 0.1, 0.1, 0.2],
        "sequence_length": 5,
        "num_predictions": 1,
    }
    response = inference_client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert data["predictions"] == [22.4]
