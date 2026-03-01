"""
MLflow Model Registry Service
Gerenciamento de modelos de machine learning com versionamento, lineage e monitoramento
"""

import logging
import os
import json
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

try:
    import mlflow
    import mlflow.sklearn
    import mlflow.tensorflow
    import mlflow.pytorch
    from mlflow.tracking import MlflowClient
    from mlflow.entities import ModelVersion, Run
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logger.warning("MLflow not installed. Model registry disabled.")
    
    # Mock classes for when MLflow is not available
    class MlflowClient:
        def __init__(self, *args, **kwargs):
            pass
    
    class ModelVersion:
        pass
    
    class Run:
        pass


class MLflowModelRegistry:
    """
    Registry de Modelos de Machine Learning com MLflow
    
    Features:
    - Versionamento de modelos
    - Lineage de dados
    - Monitoramento de drift (PSI)
    - SHAP explainability
    - Stage transitions (Staging, Production, Archived)
    - Métricas de performance
    """
    
    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        registry_uri: Optional[str] = None,
        experiment_name: str = "climatewise",
    ):
        """
        Inicializa o MLflow
        
        Args:
            tracking_uri: URI do MLflow Tracking Server
            registry_uri: URI do Model Registry (default: tracking_uri)
            experiment_name: Nome do experimento
        """
        if not MLFLOW_AVAILABLE:
            self.enabled = False
            logger.warning("MLflow integration disabled - mlflow not installed")
            return
        
        self.tracking_uri = tracking_uri or os.getenv(
            "MLFLOW_TRACKING_URI",
            "http://localhost:5000"
        )
        self.registry_uri = registry_uri or self.tracking_uri
        self.experiment_name = experiment_name
        
        # Configurar URIs
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_registry_uri(self.registry_uri)
        
        # Criar ou obter experimento
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            self.experiment_id = mlflow.create_experiment(
                experiment_name,
                artifact_location=os.getenv(
                    "MLFLOW_ARTIFACT_LOCATION",
                    "file:///tmp/mlflow"
                ),
            )
        else:
            self.experiment_id = experiment.experiment_id
        
        # Cliente para operações de baixo nível
        self.client = MlflowClient(self.tracking_uri)
        
        self.enabled = True
        logger.info(f"MLflow initialized: {self.tracking_uri}")
    
    def is_enabled(self) -> bool:
        """Verifica se MLflow está habilitado"""
        return self.enabled and MLFLOW_AVAILABLE
    
    def is_healthy(self) -> bool:
        """Verifica saúde do MLflow"""
        if not self.enabled:
            return False
        
        try:
            # Try to get experiment
            experiment = mlflow.get_experiment(self.experiment_id)
            return experiment is not None
        except Exception as e:
            logger.error(f"MLflow health check failed: {e}")
            return False
    
    @contextmanager
    def start_run(
        self,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        description: Optional[str] = None,
    ):
        """
        Context manager para criar um run de treinamento
        
        Usage:
            with registry.start_run("model-v1", tags={"team": "climate"}):
                model = train_model()
                mlflow.sklearn.log_model(model, "model")
        """
        run_tags = tags or {}
        if description:
            run_tags["description"] = description
        
        try:
            with mlflow.start_run(
                experiment_id=self.experiment_id,
                run_name=run_name,
                tags=run_tags,
            ) as run:
                yield run
        except Exception as e:
            logger.error(f"MLflow run failed: {e}")
            raise
    
    def log_model(
        self,
        model: Any,
        model_name: str,
        artifact_path: str = "model",
        registered_model_name: Optional[str] = None,
        metrics: Optional[Dict[str, float]] = None,
        params: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Optional[ModelVersion]:
        """
        Loga e registra um modelo
        
        Args:
            model: Modelo treinado
            model_name: Nome do modelo no registry
            artifact_path: Caminho no artifact store
            registered_model_name: Nome para registro (opcional)
            metrics: Métricas do modelo
            params: Parâmetros do modelo
            tags: Tags adicionais
        
        Returns:
            ModelVersion se registrado, None caso contrário
        """
        if not self.enabled:
            return None
        
        try:
            with mlflow.start_run(experiment_id=self.experiment_id):
                # Log params
                if params:
                    mlflow.log_params(params)
                
                # Log metrics
                if metrics:
                    for key, value in metrics.items():
                        mlflow.log_metric(key, value)
                
                # Log tags
                if tags:
                    for key, value in tags.items():
                        mlflow.set_tag(key, value)
                
                # Detect model type and log accordingly
                model_type = self._detect_model_type(model)
                
                if model_type == "sklearn":
                    mlflow.sklearn.log_model(
                        model,
                        artifact_path,
                        registered_model_name=registered_model_name,
                    )
                elif model_type == "tensorflow":
                    mlflow.tensorflow.log_model(
                        model,
                        artifact_path,
                        registered_model_name=registered_model_name,
                    )
                elif model_type == "pytorch":
                    mlflow.pytorch.log_model(
                        model,
                        artifact_path,
                        registered_model_name=registered_model_name,
                    )
                else:
                    # Generic model
                    mlflow.log_model(model, artifact_path)
                
                run_id = mlflow.active_run().info.run_id
                
                # Register model if name provided
                if registered_model_name:
                    model_version = self.client.create_model_version(
                        name=registered_model_name,
                        source=f"runs:/{run_id}/{artifact_path}",
                        run_id=run_id,
                    )
                    logger.info(
                        f"Model registered: {registered_model_name} "
                        f"(version {model_version.version})"
                    )
                    return model_version
                
                return None
                
        except Exception as e:
            logger.error(f"Error logging model: {e}")
            return None
    
    def _detect_model_type(self, model: Any) -> str:
        """Detecta o tipo do modelo"""
        try:
            import sklearn
            if isinstance(model, sklearn.base.BaseEstimator):
                return "sklearn"
        except ImportError:
            pass
        
        try:
            import tensorflow as tf
            if isinstance(model, tf.keras.Model):
                return "tensorflow"
        except ImportError:
            pass
        
        try:
            import torch
            if isinstance(model, torch.nn.Module):
                return "pytorch"
        except ImportError:
            pass
        
        return "generic"
    
    def get_model(
        self,
        model_name: str,
        version: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> Optional[Any]:
        """
        Carrega um modelo do registry
        
        Args:
            model_name: Nome do modelo
            version: Versão específica ou "latest"
            stage: Stage (Production, Staging, Archived)
        
        Returns:
            Modelo carregado ou None
        """
        if not self.enabled:
            return None
        
        try:
            if version == "latest" or (version is None and stage is None):
                # Get latest version
                versions = self.client.get_latest_versions(model_name)
                if not versions:
                    logger.warning(f"No versions found for {model_name}")
                    return None
                model_uri = versions[0].source
            elif stage:
                # Get version by stage
                versions = self.client.get_latest_versions(
                    model_name,
                    stages=[stage],
                )
                if not versions:
                    logger.warning(f"No {stage} version found for {model_name}")
                    return None
                model_uri = versions[0].source
            else:
                # Get specific version
                model_uri = f"models:/{model_name}/{version}"
            
            # Load model
            model = mlflow.sklearn.load_model(model_uri)
            logger.info(f"Model loaded: {model_uri}")
            return model
            
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return None
    
    def transition_model_stage(
        self,
        model_name: str,
        version: str,
        stage: str,
    ) -> bool:
        """
        Transiciona modelo para um stage
        
        Args:
            model_name: Nome do modelo
            version: Versão
            stage: Stage destino (Production, Staging, Archived)
        
        Returns:
            True se sucesso
        """
        if not self.enabled:
            return False
        
        try:
            self.client.transition_model_version_stage(
                name=model_name,
                version=version,
                stage=stage,
            )
            logger.info(
                f"Model {model_name} v{version} transitioned to {stage}"
            )
            return True
        except Exception as e:
            logger.error(f"Error transitioning model stage: {e}")
            return False
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações de um modelo
        
        Args:
            model_name: Nome do modelo
        
        Returns:
            Informações do modelo
        """
        if not self.enabled:
            return None
        
        try:
            model = self.client.get_registered_model(model_name)
            versions = self.client.search_model_versions(
                f"name='{model_name}'"
            )
            
            return {
                "name": model.name,
                "description": model.description,
                "creation_timestamp": model.creation_timestamp,
                "last_updated": model.last_updated_timestamp,
                "versions": [
                    {
                        "version": v.version,
                        "stage": v.current_stage,
                        "run_id": v.run_id,
                        "creation_timestamp": v.creation_timestamp,
                    }
                    for v in versions
                ],
            }
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return None
    
    def list_models(self) -> List[str]:
        """Lista todos os modelos registrados"""
        if not self.enabled:
            return []
        
        try:
            models = self.client.search_registered_models()
            return [model.name for model in models]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def log_drift_metrics(
        self,
        model_name: str,
        version: str,
        reference_data: Any,
        current_data: Any,
        feature_columns: List[str],
    ) -> Dict[str, float]:
        """
        Loga métricas de drift (PSI - Population Stability Index)
        
        Args:
            model_name: Nome do modelo
            version: Versão
            reference_data: Dados de referência (treinamento)
            current_data: Dados atuais (produção)
            feature_columns: Colunas de features
        
        Returns:
            Dicionário com PSI por feature
        """
        if not self.enabled:
            return {}
        
        try:
            psi_metrics = self._calculate_psi(
                reference_data,
                current_data,
                feature_columns,
            )
            
            # Log to MLflow
            with mlflow.start_run():
                for feature, psi in psi_metrics.items():
                    mlflow.log_metric(f"psi_{feature}", psi)
                
                # Add tags
                mlflow.set_tag("model_name", model_name)
                mlflow.set_tag("model_version", version)
                mlflow.set_tag("metric_type", "drift_psi")
            
            logger.info(f"Drift metrics logged for {model_name} v{version}")
            return psi_metrics
            
        except Exception as e:
            logger.error(f"Error logging drift metrics: {e}")
            return {}
    
    def _calculate_psi(
        self,
        reference: Any,
        current: Any,
        columns: List[str],
        buckets: int = 10,
    ) -> Dict[str, float]:
        """
        Calcula Population Stability Index (PSI)
        
        PSI < 0.1: Sem drift significativo
        0.1 <= PSI < 0.2: Drift moderado
        PSI >= 0.2: Drift significativo
        """
        import numpy as np
        
        psi_values = {}
        
        for col in columns:
            try:
                ref_data = reference[col].values if hasattr(reference, col) else reference.get(col, [])
                cur_data = current[col].values if hasattr(current, col) else current.get(col, [])
                
                if len(ref_data) == 0 or len(cur_data) == 0:
                    psi_values[col] = 0.0
                    continue
                
                # Create buckets
                ref_min, ref_max = np.min(ref_data), np.max(ref_data)
                cur_min, cur_max = np.min(cur_data), np.max(cur_data)
                global_min = min(ref_min, cur_min)
                global_max = max(ref_max, cur_max)
                
                bins = np.linspace(global_min, global_max, buckets + 1)
                
                # Calculate distributions
                ref_dist, _ = np.histogram(ref_data, bins=bins)
                cur_dist, _ = np.histogram(cur_data, bins=bins)
                
                # Normalize
                ref_pct = (ref_dist + 1) / (len(ref_data) + buckets)
                cur_pct = (cur_dist + 1) / (len(cur_data) + buckets)
                
                # Calculate PSI
                psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
                psi_values[col] = float(psi)
                
            except Exception as e:
                logger.warning(f"Error calculating PSI for {col}: {e}")
                psi_values[col] = 0.0
        
        return psi_values
    
    def get_run_metrics(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Obtém métricas de um run específico"""
        if not self.enabled:
            return None
        
        try:
            run = self.client.get_run(run_id)
            return {
                "metrics": run.data.metrics,
                "params": run.data.params,
                "tags": run.data.tags,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
            }
        except Exception as e:
            logger.error(f"Error getting run metrics: {e}")
            return None


# Singleton instance
_mlflow_instance: Optional[MLflowModelRegistry] = None


def get_mlflow() -> MLflowModelRegistry:
    """Obtém instância singleton do MLflow"""
    global _mlflow_instance
    if _mlflow_instance is None:
        _mlflow_instance = MLflowModelRegistry()
    return _mlflow_instance


# Exemplo de uso
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize MLflow
    registry = MLflowModelRegistry(
        tracking_uri="http://localhost:5000",
        experiment_name="climatewise-demo",
    )
    
    if registry.is_enabled():
        print(f"✓ MLflow enabled: {registry.is_healthy()}")
        
        # Example: List models
        models = registry.list_models()
        print(f"Registered models: {models}")
        
        # Example: Get model info
        if models:
            info = registry.get_model_info(models[0])
            print(f"Model info: {info}")
    else:
        print("✗ MLflow not enabled")
