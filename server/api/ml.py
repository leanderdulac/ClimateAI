"""
Machine Learning Router - Endpoints para predição e treinamento de modelos ML
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from services.audit_service import log_operation
from services.ml_service import get_ml_model_info, predict_sinistrality, train_ml_models

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/predict-sinistrality")
async def predict_sinistrality_endpoint(features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prediz frequência e severidade de sinistros usando machine learning

    Args:
        features: Dicionário com características para predição
            - rainfall: Precipitação (mm)
            - temperature: Temperatura (°C)
            - humidity: Umidade (%)
            - inflation_rate: Taxa de inflação
            - gdp_growth: Crescimento do PIB
            - latitude: Latitude
            - longitude: Longitude
            - month: Mês (opcional)

    Returns:
        Predições de frequência e severidade com intervalos de confiança
    """
    try:
        result = predict_sinistrality(features)

        # Registrar operação de auditoria
        log_operation(
            operation="ml_prediction",
            resource_type="risk_model",
            action="predict",
            status="success",
            details={"features": features, "predictions": result},
            risk_score=result.get("risk_score", 0),
        )

        return result
    except Exception as e:
        # Registrar erro de auditoria
        log_operation(
            operation="ml_prediction",
            resource_type="risk_model",
            action="predict",
            status="error",
            details={"error": str(e), "features": features},
            compliance_flags=["ml_prediction_error"],
        )
        logger.error(f"Erro na predição ML: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na predição: {str(e)}")


@router.post("/train-models")
async def train_ml_models_endpoint(
    data: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Treina os modelos de machine learning para predição de sinistralidade

    Args:
        data: Dados históricos opcionais para treinamento

    Returns:
        Métricas de treinamento e status
    """
    try:
        import pandas as pd

        df = pd.DataFrame(data) if data else None
        result = train_ml_models(df)
        return result
    except Exception as e:
        logger.error(f"Erro no treinamento ML: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no treinamento: {str(e)}")


@router.get("/model-info")
async def get_ml_model_info_endpoint() -> Dict[str, Any]:
    """
    Retorna informações sobre os modelos de machine learning

    Returns:
        Status dos modelos e informações de treinamento
    """
    try:
        return get_ml_model_info()
    except Exception as e:
        logger.error(f"Erro ao obter info do modelo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter info: {str(e)}")
