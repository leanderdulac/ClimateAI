"""
AI Services Subpackage
Contains machine learning and AI-related services.
Imports are lazy to allow the server to start without heavy ML dependencies (torch, tensorflow).
"""

import logging

logger = logging.getLogger(__name__)

# Lazy imports — these modules require heavy ML libraries (torch, tensorflow, etc.)
# They will only be imported when explicitly accessed.
try:
    from services.decision_flow_service import DecisionFlowService
except ImportError as e:
    logger.warning(f"DecisionFlowService unavailable: {e}")
    DecisionFlowService = None

try:
    from services.gemini_integration_service import GeminiIntegrationService
except (ImportError, ValueError) as e:
    logger.warning(f"GeminiIntegrationService unavailable: {e}")
    GeminiIntegrationService = None

try:
    from services.ia_analytics_agent_service import IAAnalyticsAgentService
except ImportError as e:
    logger.warning(f"IAAnalyticsAgentService unavailable: {e}")
    IAAnalyticsAgentService = None

try:
    from services.lstm_attention_service import LSTMAttentionService
except ImportError as e:
    logger.warning(f"LSTMAttentionService unavailable (torch not installed): {e}")
    LSTMAttentionService = None

try:
    from services.ml_service import (
        get_ml_model_info,
        predict_sinistrality,
        sinistrality_predictor,
        train_ml_models,
    )
except ImportError as e:
    logger.warning(f"ML service unavailable: {e}")
    predict_sinistrality = None
    train_ml_models = None
    get_ml_model_info = None
    sinistrality_predictor = None

__all__ = [
    "predict_sinistrality",
    "train_ml_models",
    "get_ml_model_info",
    "sinistrality_predictor",
    "LSTMAttentionService",
    "GeminiIntegrationService",
    "IAAnalyticsAgentService",
    "DecisionFlowService",
]
