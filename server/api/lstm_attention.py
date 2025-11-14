"""
Router for LSTM Attention Service for Climate Time Series Prediction
Implements h_t = LSTM(x_t, h_{t-1}), α_t = softmax(v^T tanh(W_h h_t + W_c c_t)), ŷ = Σ_t α_t · h_t
Where x_t = [temp_t, precip_t, pressão_t, índice_NAO, fase_ENSO]
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np

from services.lstm_attention_service import (
    climate_attention_service,
    prepare_climate_features,
    train_lstm_attention_model,
    predict_with_lstm_attention,
    predict_with_attention_visualization
)

router = APIRouter()

@router.post("/lstm-attention/prepare-features")
async def prepare_climate_features_endpoint(
    temperature: List[float],
    precipitation: List[float], 
    pressure: List[float],
    nao_index: List[float],
    enso_phase: List[float]
):
    """
    Prepare climate features in the format x_t = [temp_t, precip_t, pressão_t, índice_NAO, fase_ENSO]
    """
    try:
        result = prepare_climate_features(
            temperature, precipitation, pressure, nao_index, enso_phase
        )
        return {
            "features": result.tolist(),
            "n_samples": result.shape[0],
            "n_features": result.shape[1],
            "feature_names": ["temperature", "precipitation", "pressure", "nao_index", "enso_phase"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature preparation failed: {str(e)}")

@router.post("/lstm-attention/train")
async def train_lstm_attention_endpoint(
    temperature: List[float],
    precipitation: List[float],
    pressure: List[float], 
    nao_index: List[float],
    enso_phase: List[float],
    targets: List[float],
    sequence_length: int = Query(10, ge=3, le=50, description="Length of input sequences"),
    epochs: int = Query(50, ge=1, le=500, description="Number of training epochs"),
    batch_size: int = Query(32, ge=1, le=256, description="Training batch size"),
    validation_split: float = Query(0.2, ge=0.0, le=0.5, description="Validation split fraction")
):
    """
    Train the LSTM attention model for climate prediction:
    h_t = LSTM(x_t, h_{t-1})
    α_t = softmax(v^T tanh(W_h h_t + W_c c_t)) 
    ŷ = Σ_t α_t · h_t
    Where x_t = [temp_t, precip_t, pressão_t, índice_NAO, fase_ENSO]
    """
    try:
        result = train_lstm_attention_model(
            temperature, precipitation, pressure, nao_index, enso_phase,
            targets, sequence_length, epochs, batch_size, validation_split
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LSTM attention model training failed: {str(e)}")

@router.post("/lstm-attention/predict")
async def predict_lstm_attention_endpoint(
    temperature: List[float],
    precipitation: List[float],
    pressure: List[float],
    nao_index: List[float], 
    enso_phase: List[float],
    sequence_length: int = Query(10, ge=3, le=50, description="Length of input sequences")
):
    """
    Make predictions using the trained LSTM attention model
    """
    try:
        result = predict_with_lstm_attention(
            temperature, precipitation, pressure, nao_index, enso_phase, sequence_length
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LSTM attention prediction failed: {str(e)}")

@router.post("/lstm-attention/predict-with-attention")
async def predict_with_attention_visualization_endpoint(
    temperature: List[float],
    precipitation: List[float],
    pressure: List[float],
    nao_index: List[float],
    enso_phase: List[float], 
    targets: List[float],
    sequence_length: int = Query(10, ge=3, le=50, description="Length of input sequences")
):
    """
    Make predictions with detailed attention visualization for climate time series
    """
    try:
        result = predict_with_attention_visualization(
            temperature, precipitation, pressure, nao_index, enso_phase,
            targets, sequence_length
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Attention visualization prediction failed: {str(e)}")

@router.get("/lstm-attention/status")
async def lstm_attention_status():
    """
    Get the status of the LSTM attention model
    """
    return {
        "model_exists": climate_attention_service.model is not None,
        "is_trained": climate_attention_service.is_trained,
        "model_trained": climate_attention_service.is_trained,
        "timestamp": datetime.now().isoformat()
    }