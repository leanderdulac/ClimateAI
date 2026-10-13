"""Unit tests for ModelRegistryService."""

import pytest
import tempfile
import os
from services.model_registry_service import (
    ModelRegistryService,
    ModelStage,
    ModelVersion,
)


def test_model_registry_initialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        reg_path = os.path.join(tmpdir, "test_registry.json")
        service = ModelRegistryService(registry_file=reg_path)

        models = service.list_models()
        assert "climate_lstm_attention" in models
        assert "poseidon_cco" in models

        prod_model = service.get_production_model("climate_lstm_attention")
        assert prod_model is not None
        assert prod_model.stage == ModelStage.PRODUCTION
        assert prod_model.version == "1.0.0"


def test_model_registry_registration_and_promotion():
    with tempfile.TemporaryDirectory() as tmpdir:
        reg_path = os.path.join(tmpdir, "test_registry.json")
        service = ModelRegistryService(registry_file=reg_path)

        new_v = service.register_model_version(
            model_name="climate_lstm_attention",
            version="1.1.0",
            artifact_bytes=b"dummy_weights_v1.1",
            metrics={"rmse": 0.095, "mae": 0.071, "r2": 0.965},
            promote_to_production=True,
        )

        assert new_v.stage == ModelStage.PRODUCTION
        assert new_v.version == "1.1.0"

        active = service.get_production_model("climate_lstm_attention")
        assert active.version == "1.1.0"


def test_model_registry_safe_rollback():
    with tempfile.TemporaryDirectory() as tmpdir:
        reg_path = os.path.join(tmpdir, "test_registry.json")
        service = ModelRegistryService(registry_file=reg_path)

        # Register and promote v1.1.0
        service.register_model_version(
            model_name="climate_lstm_attention",
            version="1.1.0",
            artifact_bytes=b"v1.1",
            metrics={"rmse": 0.09},
            promote_to_production=True,
        )

        # Rollback
        rolled_back = service.rollback_production_model("climate_lstm_attention")
        assert rolled_back is not None
        assert rolled_back.version == "1.0.0"
        assert rolled_back.stage == ModelStage.PRODUCTION
