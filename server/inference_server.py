"""
Standalone MLOps Inference Service for ClimateWise
Decoupled high-performance inference server for PyTorch LSTM-Attention & ML models.
Exposes endpoints for prediction and health monitoring with dedicated CPU/GPU allocation.
"""

from __future__ import annotations

import logging
import os
os.environ["IS_INFERENCE_SERVICE"] = "1"
os.environ.pop("INFERENCE_SERVICE_URL", None)

from typing import Any, Dict, List, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from services.lstm_attention_service import (
    LSTMAttentionService,
    select_torch_device,
    HAS_TORCH,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inference_service")

app = FastAPI(
    title="ClimateWise MLOps Inference Service",
    description="Dedicated microservice for heavy deep learning and time-series climate inference",
    version="1.0.0",
)

# Shared in-memory service instance
_lstm_service: Optional[LSTMAttentionService] = None


def get_lstm_service() -> LSTMAttentionService:
    global _lstm_service
    if _lstm_service is None:
        device = select_torch_device(prefer_mps=True)
        _lstm_service = LSTMAttentionService(device=device)
        logger.info("Initialized LSTMAttentionService on device: %s", device)
    return _lstm_service


class PredictRequest(BaseModel):
    temperature: List[float] = Field(..., min_length=5)
    precipitation: List[float] = Field(..., min_length=5)
    pressure: List[float] = Field(..., min_length=5)
    nao_index: List[float] = Field(..., min_length=5)
    enso_phase: List[float] = Field(..., min_length=5)
    sequence_length: int = Field(default=10, ge=3, le=100)
    num_predictions: int = Field(default=1, ge=1, le=30)


class TrainRequest(BaseModel):
    features: List[List[float]]
    targets: List[float]
    epochs: int = Field(default=20, ge=1, le=200)
    batch_size: int = Field(default=16, ge=1, le=128)
    sequence_length: int = Field(default=10, ge=3, le=100)


@app.get("/health")
async def health() -> Dict[str, Any]:
    device = select_torch_device(prefer_mps=True)
    return {
        "status": "healthy",
        "service": "climatewise-inference-engine",
        "has_torch": HAS_TORCH,
        "device": str(device) if device is not None else "cpu",
    }


@app.get("/status")
async def status_endpoint() -> Dict[str, Any]:
    svc = get_lstm_service()
    return {
        "status": "online",
        "is_trained": svc.is_trained,
        "device": str(svc.device) if svc.device is not None else "cpu",
        "has_torch": HAS_TORCH,
    }


@app.post("/predict")
async def predict_endpoint(payload: PredictRequest) -> Dict[str, Any]:
    svc = get_lstm_service()
    if not svc.is_trained:
        # Auto-train on synthetic baseline if untrained so inference is always ready
        logger.info("Model untrained; performing quick bootstrap training on baseline data")
        seq_len = min(len(payload.temperature) // 2, payload.sequence_length)
        targets = payload.temperature  # predict temperature
        svc.train_model(
            temperature=payload.temperature,
            precipitation=payload.precipitation,
            pressure=payload.pressure,
            nao_index=payload.nao_index,
            enso_phase=payload.enso_phase,
            targets=targets,
            epochs=2,
            batch_size=4,
            sequence_length=max(3, seq_len),
        )

    try:
        result = svc.predict(
            temperature=payload.temperature,
            precipitation=payload.precipitation,
            pressure=payload.pressure,
            nao_index=payload.nao_index,
            enso_phase=payload.enso_phase,
            sequence_length=payload.sequence_length,
            num_predictions=payload.num_predictions,
        )
        return _to_serializable(result)
    except Exception as exc:
        logger.error("Inference failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference computation error: {exc}",
        ) from exc


def _to_serializable(obj: Any) -> Any:
    if hasattr(obj, "tolist"):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_serializable(v) for v in obj]
    return obj


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
