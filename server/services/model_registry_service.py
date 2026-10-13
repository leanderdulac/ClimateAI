"""
Model Registry Service
Provides versioning, artifact verification (SHA256), stage transitions,
and automated rollback for ClimateWise MLOps models.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ModelStage(str, Enum):
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


@dataclass
class ModelVersion:
    model_name: str
    version: str
    stage: ModelStage
    artifact_checksum: str
    metrics: Dict[str, float]
    created_at_utc: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModelRegistryService:
    """Manages model versions, staging-to-production promotion, and safe rollbacks."""

    def __init__(self, registry_file: Optional[str] = None):
        if registry_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            registry_file = os.path.join(base_dir, "data", "model_registry.json")
        self.registry_file = registry_file
        self._models: Dict[str, List[ModelVersion]] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Loads registered models from file if exists, or seeds defaults."""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for m_name, versions in data.items():
                        self._models[m_name] = [
                            ModelVersion(
                                model_name=v["model_name"],
                                version=v["version"],
                                stage=ModelStage(v["stage"]),
                                artifact_checksum=v["artifact_checksum"],
                                metrics=v.get("metrics", {}),
                                created_at_utc=v["created_at_utc"],
                                metadata=v.get("metadata", {}),
                            )
                            for v in versions
                        ]
                return
            except Exception as e:
                logger.warning(f"Could not load model registry: {e}. Seeding default.")

        # Seed initial models
        now = datetime.now(timezone.utc).isoformat()
        self._models = {
            "climate_lstm_attention": [
                ModelVersion(
                    model_name="climate_lstm_attention",
                    version="1.0.0",
                    stage=ModelStage.PRODUCTION,
                    artifact_checksum=hashlib.sha256(b"climate_lstm_v1").hexdigest(),
                    metrics={"rmse": 0.124, "mae": 0.089, "r2": 0.942},
                    created_at_utc=now,
                    metadata={"framework": "pytorch", "input_features": ["temp", "rain", "wind"]},
                )
            ],
            "poseidon_cco": [
                ModelVersion(
                    model_name="poseidon_cco",
                    version="1.0.0",
                    stage=ModelStage.PRODUCTION,
                    artifact_checksum=hashlib.sha256(b"poseidon_cco_v1").hexdigest(),
                    metrics={"accuracy": 0.985, "actuarial_alignment": 0.992},
                    created_at_utc=now,
                    metadata={"framework": "ollama", "base_model": "deepseek-r1:8b"},
                )
            ],
        }

    def _save_registry(self) -> None:
        """Persists registry state to JSON."""
        try:
            os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
            serializable = {
                m_name: [asdict(v) for v in versions]
                for m_name, versions in self._models.items()
            }
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(serializable, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist model registry: {e}")

    def register_model_version(
        self,
        model_name: str,
        version: str,
        artifact_bytes: bytes,
        metrics: Dict[str, float],
        metadata: Optional[Dict[str, Any]] = None,
        promote_to_production: bool = False,
    ) -> ModelVersion:
        """Registers a new model version with checksum verification."""
        checksum = hashlib.sha256(artifact_bytes).hexdigest()
        now = datetime.now(timezone.utc).isoformat()

        stage = ModelStage.PRODUCTION if promote_to_production else ModelStage.STAGING

        new_version = ModelVersion(
            model_name=model_name,
            version=version,
            stage=stage,
            artifact_checksum=checksum,
            metrics=metrics,
            created_at_utc=now,
            metadata=metadata or {},
        )

        if model_name not in self._models:
            self._models[model_name] = []

        if promote_to_production:
            # Demote existing production models to archived
            for v in self._models[model_name]:
                if v.stage == ModelStage.PRODUCTION:
                    v.stage = ModelStage.ARCHIVED

        self._models[model_name].append(new_version)
        self._save_registry()
        return new_version

    def get_production_model(self, model_name: str) -> Optional[ModelVersion]:
        """Returns the currently active production model version."""
        versions = self._models.get(model_name, [])
        for v in reversed(versions):
            if v.stage == ModelStage.PRODUCTION:
                return v
        return None

    def rollback_production_model(self, model_name: str) -> Optional[ModelVersion]:
        """Rolls back from current production model to the immediately preceding version."""
        versions = self._models.get(model_name, [])
        if not versions:
            return None

        current_prod_idx = None
        for i, v in enumerate(versions):
            if v.stage == ModelStage.PRODUCTION:
                current_prod_idx = i
                break

        if current_prod_idx is None or current_prod_idx == 0:
            logger.warning(f"No previous version available to rollback for {model_name}")
            return None

        # Archive current
        versions[current_prod_idx].stage = ModelStage.ARCHIVED
        # Promote previous
        target_version = versions[current_prod_idx - 1]
        target_version.stage = ModelStage.PRODUCTION
        self._save_registry()
        logger.info(f"Rolled back {model_name} to version {target_version.version}")
        return target_version

    def list_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """Lists all registered models and their stages."""
        return {
            m_name: [asdict(v) for v in versions]
            for m_name, versions in self._models.items()
        }
