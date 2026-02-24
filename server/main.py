"""
Framework Integrado de Modelagem Climático-Econômica (FIMCE)
Servidor principal do sistema de previsão climática e modelagem de preços
"""

import hashlib
import logging
import os
import time
import uuid
from functools import lru_cache
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Carregar variáveis de ambiente ANTES de qualquer import
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Importar health checker
from api.health import HealthChecker

# Importar logging estruturado
from api.logging import (
    LogCategory,
    LogContext,
    LoggingMiddleware,
    StructuredLogger,
    get_logger,
    get_structured_logger,
    init_logging,
    setup_json_logging,
)

# Inicializar logging
init_logging()
logger = get_logger()

from config.config import settings

# Importar módulos de segurança
from lib.security import SecurityConfig, rate_limiter
from middleware.security_middleware import SecurityHeadersMiddleware

from services.otel import init_otel
from middleware.redaction import redact_payload

# ============================================
# SECRETS MANAGER - HashiCorp Vault (Tier 1)
# ============================================
from lib.vault_secrets import get_vault, VaultSecretsManager

# Inicializar Vault Secrets Manager
vault_manager: Optional[VaultSecretsManager] = None
try:
    vault_manager = get_vault()
    if vault_manager.is_enabled():
        logger.info(f"✓ Vault Secrets Manager initialized: {vault_manager.url}")
    else:
        logger.warning("⚠ Vault Secrets Manager disabled (VAULT_TOKEN not configured)")
except Exception as e:
    logger.warning(f"⚠ Vault Secrets Manager initialization skipped: {e}")

# ============================================
# MLFLOW MODEL REGISTRY (Tier 1)
# ============================================
from lib.mlflow_registry import get_mlflow, MLflowModelRegistry

# Inicializar MLflow Model Registry
mlflow_registry: Optional[MLflowModelRegistry] = None
try:
    mlflow_registry = get_mlflow()
    if mlflow_registry.is_enabled():
        logger.info(f"✓ MLflow Model Registry initialized: {mlflow_registry.tracking_uri}")
    else:
        logger.warning("⚠ MLflow Model Registry disabled (MLflow not installed)")
except Exception as e:
    logger.warning(f"⚠ MLflow Model Registry initialization skipped: {e}")

# Sistema de Cache Inteligente
class SmartCache:
    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_ttls = {}  # Per-entry TTL
        self.default_max_age = 3600  # 1 hora por padrão

    def _generate_key(self, data: Any) -> str:
        """Gera uma chave única para os dados"""
        if isinstance(data, dict):
            # Ordena as chaves para consistência
            sorted_data = str(sorted(data.items()))
        else:
            sorted_data = str(data)
        return hashlib.md5(sorted_data.encode()).hexdigest()

    def _get_ttl(self, key: str) -> int:
        """Retorna o TTL para uma entrada específica"""
        return self.cache_ttls.get(key, self.default_max_age)

    def get(self, key: str) -> Optional[Any]:
        """Recupera dados do cache se ainda válidos"""
        if key in self.cache:
            timestamp = self.cache_timestamps.get(key, 0)
            ttl = self._get_ttl(key)
            if time.time() - timestamp < ttl:
                logger.info(f"Cache hit for key: {key[:8]}...")
                return self.cache[key]
            else:
                # Remove entrada expirada
                del self.cache[key]
                del self.cache_timestamps[key]
                self.cache_ttls.pop(key, None)
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Armazena dados no cache"""
        self.cache[key] = value
        self.cache_timestamps[key] = time.time()
        if ttl:
            self.cache_ttls[key] = ttl
        logger.info(f"Cached data for key: {key[:8]}...")

    def clear_expired(self) -> None:
        """Remove entradas expiradas do cache"""
        current_time = time.time()
        expired_keys = [
            key
            for key, timestamp in self.cache_timestamps.items()
            if current_time - timestamp >= self._get_ttl(key)
        ]
        for key in expired_keys:
            del self.cache[key]
            del self.cache_timestamps[key]
            self.cache_ttls.pop(key, None)
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")


# Instância global do cache
smart_cache = SmartCache()

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import Query

# Importar Pydantic models para pricing
from pydantic import BaseModel

from api.alertas import router as alertas_router
from api.auth import router as auth_router
from api.audit import router as audit_router
from api.backtesting import router as backtesting_router
from api.bayesian_bootstrap import router as bayesian_bootstrap_router
from api.blockchain_tokens import router as blockchain_tokens_router
from api.cache import router as cache_router
from api.cache import set_cache_instance

# Importar routers e configurações
# Obs: Logging será inicializado após a criação do app FastAPI
from api.clima import router as clima_router
from api.climate_alert import router as climate_alert_router
from api.climate_capital_charge import router as climate_capital_charge_router
from api.climate_hmm import router as climate_hmm_router
from api.climate_premium import router as climate_premium_router
from api.climate_risk_analysis import router as climate_risk_analysis_router
from api.climate_risk_modeling import router as climate_risk_modeling_router
from api.climate_risk_report import router as climate_risk_report_router
from api.climate_scr import router as climate_scr_router
from api.comprehensive_pricing import router as comprehensive_pricing_router
from api.concentration_risk import router as concentration_risk_router
from api.dynamic_insurance_analysis import router as dynamic_insurance_analysis_router
try:
    from api.dynamical_climate import router as dynamical_climate_router
except ImportError:
    dynamical_climate_router = None
from api.english_api import router as english_api_router
from api.english_climateai import router as english_climateai_router
from api.ensemble_pricing import router as ensemble_pricing_router
from api.eventos import router as eventos_router
from api.external import router as external_router
from api.gemini_integration import router as gemini_integration_router
from api.grok_integration import router as grok_integration_router
from api.noaa_integration import router as noaa_integration_router
from api.xweather_forecast import router as xweather_forecast_router
from api.model_governance import router as model_governance_router
from api.regulatory_reporting import router as regulatory_reporting_router
from api.inmet_alertas import router as inmet_alertas_router
from api.brazil_disaster_alerts import router as brazil_disaster_alerts_router
from api.parametric_trigger_verification import router as parametric_trigger_router
from api.i18n import router as i18n_router
from api.ia_analytics_agent import router as ia_analytics_agent_router
from api.integrated_pipeline import router as integrated_pipeline_router
from api.integrated_pricing_framework import (
    router as integrated_pricing_framework_router,
)
from api.investment_return import router as investment_return_router
from api.lei_analysis import router as lei_analysis_router
from api.loading_margin import router as loading_margin_router
from api.localizacao import router as localizacao_router
try:
    from api.lstm_attention import router as lstm_attention_router
except ImportError:
    lstm_attention_router = None
from api.mathematical_engines import router as mathematical_engines_router
from api.microsegmentation import router as microsegmentation_router
from api.mitigation_measures import router as mitigation_measures_router
try:
    from api.ml import router as ml_router
except ImportError:
    ml_router = None
from api.modelagem import router as modelagem_router
from api.operating_costs import router as operating_costs_router
from api.parametric import router as parametric_router
from api.transparency import router as transparency_router
from api.carbon import router as carbon_router
from api.parametric_insurance import router as parametric_insurance_router
from api.performance_testing import router as performance_testing_router
from api.physical_risk import router as physical_risk_router
from api.policy_pricing import router as policy_pricing_router
from api.policy_uncertainty import router as policy_uncertainty_router
from api.policy_valuation import router as policy_valuation_router
from api.policy_risk_monitor import router as policy_risk_monitor_router
from api.probabilistic_climate_scenarios import router as probabilistic_climate_scenarios_router
from api.previsao import router as previsao_router
from api.pricing import router as pricing_router
from api.extreme_value_pricing import router as extreme_value_pricing_router
from api.sips_performance_analytics import router as sips_performance_analytics_router
from api.smart_exclusions import router as smart_exclusions_router
from api.tcfd_issb import router as tcfd_issb_router
from api.tokenizacao import router as tokenizacao_router
from api.transition_risk import router as transition_risk_router
from api.unified_pricing import router as unified_pricing_router
from api.xweather_forecast import router as xweather_forecast_router
from config.database import close_db, init_db
from services.audit_service import (
    get_audit_logs,
    get_compliance_report,
    log_operation,
    log_policy_decision,
    log_risk_assessment,
)
from services.dynamic_insurance_analysis_service import dynamic_analysis_service
from services.external_api_service import (
    get_commodity_prices,
    get_economic_indicators,
    get_real_time_data,
    get_weather_data,
)
from services.loading_margin_service import calculate_loading_margin
from services.microsegmentation_service import (
    analyze_location_risk,
    create_microsegments,
    get_microsegmentation_summary,
)

# from api.audit import router as audit_router
try:
    from services.ml_service import (
        get_ml_model_info,
        predict_sinistrality,
        sinistrality_predictor,
        train_ml_models,
    )
except ImportError:
    get_ml_model_info = None
    predict_sinistrality = None
    sinistrality_predictor = None
    train_ml_models = None


class PricingRequest(BaseModel):
    location_id: str
    coverage_amount: float
    coverage_period: int = 1  # em anos
    user_id: Optional[str] = None
    session_id: Optional[str] = None


# Função de cálculo de pricing aprimorada com análise dinâmica de lucratividade
def calculate_pricing(request: PricingRequest) -> Dict[str, Any]:
    """
    Calcula preço de seguro baseado em dados climáticos e fatores de risco
    Incorpora análise dinâmica de lucratividade e otimização de portfólio
    """
    from services.clima_service import ClimaService
    from services.previsao_service import PrevisaoService

    clima_service = ClimaService()
    previsao_service = PrevisaoService()

    # Obter dados climáticos para a localização
    try:
        # Obter dados históricos para análise de risco
        historico_inicio = datetime.now() - timedelta(days=365)  # Último ano
        historico_fim = datetime.now()

        # Obter dados reais de clima para análise de risco
        dados_clima = clima_service.obter_historico(
            latitude=-23.5507,  # São Paulo como exemplo
            longitude=-46.6339,
            data_inicio=historico_inicio,
            data_fim=historico_fim,
        )

        # Calcular fatores de risco com base nos dados históricos
        climatic_risk = 0.0
        economic_risk = 0.2  # Mantém valor padrão
        location_risk = 0.3  # Avaliado por sistema de microsegmentação

        if dados_clima:
            # Análise da variabilidade climática
            temps = [d.temperatura for d in dados_clima if d.temperatura is not None]
            precip = [d.precipitacao for d in dados_clima if d.precipitacao is not None]

            if temps:
                temp_variability = (
                    np.std(temps) / np.mean(temps) if np.mean(temps) != 0 else 0
                )
                climatic_risk = min(
                    1.0, temp_variability * 2
                )  # Ajuste baseado na variabilidade

            if precip:
                precip_variability = (
                    np.std(precip) / np.mean(precip) if np.mean(precip) != 0 else 0
                )
                climatic_risk = max(climatic_risk, min(1.0, precip_variability * 1.5))

        # Atualizar fatores de risco com base em dados reais
        risk_factors = {
            "climatic_risk": climatic_risk,
            "economic_risk": economic_risk,
            "location_risk": location_risk,
        }

        # Calcular prêmio dinâmico usando o novo sistema de análise
        dynamic_pricing_result = dynamic_analysis_service.calculate_dynamic_premium(
            coverage_amount=request.coverage_amount,
            risk_factors=risk_factors,
            base_loading_factor=0.20,  # 20% de loading base
        )

        # Retornar o resultado com todas as informações de análise
        return {
            "final_price": dynamic_pricing_result["final_premium"],
            "expected_claims": dynamic_pricing_result["expected_claims"],
            "profit": dynamic_pricing_result["profit"],
            "profit_margin": dynamic_pricing_result["profit_margin"],
            "break_even_premium": dynamic_pricing_result["break_even_premium"],
            "risk_score": (climatic_risk + economic_risk + location_risk) / 3,
            "risk_factors": risk_factors,
            "is_profitable": dynamic_pricing_result["is_profitable"],
            "recommendations": [
                f"Margem de lucro esperada: {dynamic_pricing_result['profit_margin']:.1%}",
                f"Prêmio mínimo para equilíbrio: R$ {dynamic_pricing_result['break_even_premium']:,.2f}",
                (
                    "Considerar cobertura adicional contra inundações"
                    if climatic_risk > 0.5
                    else ""
                ),
                (
                    "Avaliar período de cobertura mais longo"
                    if request.coverage_period == 1
                    else ""
                ),
            ],
            "compliance_flags": [],
        }
    except Exception as e:
        logger.error(f"Error in enhanced pricing calculation: {str(e)}")
        # Fallback para cálculo original em caso de erro
        return {
            "final_price": request.coverage_amount * 0.05,  # 5% do valor coberto
            "risk_score": 0.3,
            "risk_factors": {
                "climatic_risk": 0.4,
                "economic_risk": 0.2,
                "location_risk": 0.3,
            },
            "recommendations": [
                "Considerar cobertura adicional contra inundações",
                "Avaliar período de cobertura mais longo",
            ],
            "compliance_flags": [],
            "error": f"Fallback pricing used due to error: {str(e)}",
        }


# Verificar variáveis de ambiente críticas
required_env_vars = [
    ("EMBRAPA_API_KEY", "Chave da API da Embrapa"),
    ("EMBRAPA_API_URL", "URL da API da Embrapa"),
    ("EMBRAPA_API_VERSION", "Versão da API da Embrapa"),
]

missing_vars = []
for var, description in required_env_vars:
    if not os.getenv(var):
        missing_vars.append(f"{description} ({var})")
        logger.warning(f"Variável de ambiente não encontrada: {var}")

# (Imports e código inicial)
# from lib.exception_handlers import register_handlers
from middleware.error_handling import setup_error_middleware

# (Código omitido para brevidade)

# Criar a aplicação FastAPI com gestão de erros melhorada
app = FastAPI(
    title="FIMCE API",
    description="API do Framework Integrado de Modelagem Climático-Econômica",
    version="1.0.0",
    validate_responses=True,
)

# Setup advanced error handling middleware
setup_error_middleware(app)

# OpenTelemetry instrumentation (conditional)
init_otel(app)

# Configuração de CORS
# Em produção, ALLOW_ORIGINS deve ser configurado com a URL do frontend (ex: https://meu-app.netlify.app)
# Se não configurado, permite todas as origens (*) por padrão para facilitar deploy inicial
allow_origins_str = os.getenv("ALLOW_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
allow_origins = allow_origins_str.split(",") if allow_origins_str != "*" else ["*"]

# Security headers middleware (Register early to ensure headers are set even for errors)
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware (basic tracing)
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=429,
            content={"detail": "Limite de requisições excedido. Tente novamente em alguns minutos."},
            headers={
                "X-RateLimit-Limit": str(rate_limiter.max_requests),
                "X-RateLimit-Window": str(rate_limiter.window_seconds),
                "Retry-After": str(rate_limiter.window_seconds),
                "X-Request-ID": getattr(request.state, "request_id", ""),
            }
        )
    response = await call_next(request)
    response.headers["X-Request-ID"] = getattr(request.state, "request_id", "")
    return response

# Redact sensitive fields in request.state.log_context (if set by handlers)
@app.middleware("http")
async def redaction_middleware(request: Request, call_next):
    if hasattr(request.state, "log_context"):
        request.state.log_context = redact_payload(request.state.log_context)
    response = await call_next(request)
    return response
# Registrar os handlers de exceção customizados
    # register_handlers(app)

# Configuração de prefixo da API
# Em DigitalOcean, o ingress faz stripping de '/api', então o prefixo interno deve ser '/v1'
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

# (Restante do código, incluindo middlewares e routers)


# Endpoint para estatísticas do cache
@app.get(f"{API_PREFIX}/cache/stats")
async def get_cache_stats():
    """Retorna estatísticas do sistema de cache"""
    return {
        "total_entries": len(smart_cache.cache),
        "cache_size_mb": len(str(smart_cache.cache)) / (1024 * 1024),  # Aproximação
        "max_age_seconds": smart_cache.default_max_age,
        "uptime": "Sistema ativo",
    }


@app.post(f"{API_PREFIX}/cache/clear")
async def clear_cache():
    """Limpa todo o cache"""
    smart_cache.cache.clear()
    smart_cache.cache_timestamps.clear()
    return {"message": "Cache limpo com sucesso"}


# ============================================
# DEBUG ENDPOINTS
# ============================================
@app.get(f"{API_PREFIX}/debug/initialization")
async def debug_initialization():
    """Debug endpoint para verificar inicialização"""
    return {
        "vault_manager_initialized": vault_manager is not None,
        "mlflow_registry_initialized": mlflow_registry is not None,
        "vault_enabled": vault_manager.is_enabled() if vault_manager else False,
        "mlflow_enabled": mlflow_registry.is_enabled() if mlflow_registry else False,
    }


# ============================================
# SECRETS MANAGER ENDPOINTS (HashiCorp Vault)
# ============================================
@app.get(f"{API_PREFIX}/vault/status")
async def get_vault_status():
    """
    Retorna status do Vault Secrets Manager
    
    Returns:
        Status de saúde e configuração do Vault
    """
    if not vault_manager:
        return {"enabled": False, "status": "not_configured"}
    
    return {
        "enabled": vault_manager.is_enabled(),
        "healthy": vault_manager.is_healthy() if vault_manager.is_enabled() else False,
        "url": getattr(vault_manager, "url", "N/A"),
        "cache_ttl": getattr(vault_manager, "cache_ttl", 300),
    }


@app.get(f"{API_PREFIX}/vault/secrets/{{path:path}}")
async def get_vault_secret(path: str, version: Optional[int] = None):
    """
    Recupera um secret do Vault
    
    Args:
        path: Caminho do secret (ex: secret/data/climateai/api-keys)
        version: Versão específica (opcional)
    
    Returns:
        Dados do secret ou erro
    """
    if not vault_manager or not vault_manager.is_enabled():
        raise HTTPException(status_code=503, detail="Vault not enabled")
    
    secret_data = vault_manager.get_secret(path, version)
    if not secret_data:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    # Não retornar dados sensíveis diretamente
    return {
        "path": path,
        "keys": list(secret_data.keys()),
        "version": version or "latest",
    }


@app.post(f"{API_PREFIX}/vault/secrets/{{path:path}}")
async def set_vault_secret(path: str, data: Dict[str, Any]):
    """
    Armazena um secret no Vault
    
    Args:
        path: Caminho do secret
        data: Dados do secret
    
    Returns:
        Confirmação de armazenamento
    """
    if not vault_manager or not vault_manager.is_enabled():
        raise HTTPException(status_code=503, detail="Vault not enabled")
    
    success = vault_manager.set_secret(path, data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to store secret")
    
    return {"path": path, "status": "stored", "keys": list(data.keys())}


@app.delete(f"{API_PREFIX}/vault/secrets/{{path:path}}")
async def delete_vault_secret(path: str):
    """
    Deleta um secret do Vault
    
    Args:
        path: Caminho do secret
    
    Returns:
        Confirmação de deleção
    """
    if not vault_manager or not vault_manager.is_enabled():
        raise HTTPException(status_code=503, detail="Vault not enabled")
    
    success = vault_manager.delete_secret(path)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete secret")
    
    return {"path": path, "status": "deleted"}


# ============================================
# MLFLOW MODEL REGISTRY ENDPOINTS
# ============================================
@app.get(f"{API_PREFIX}/mlflow/status")
async def get_mlflow_status():
    """
    Retorna status do MLflow Model Registry
    
    Returns:
        Status de saúde e configuração do MLflow
    """
    if not mlflow_registry:
        return {"enabled": False, "status": "not_configured"}
    
    return {
        "enabled": mlflow_registry.is_enabled(),
        "healthy": mlflow_registry.is_healthy() if mlflow_registry.is_enabled() else False,
        "tracking_uri": getattr(mlflow_registry, "tracking_uri", "N/A") if mlflow_registry.is_enabled() else "N/A",
        "registry_uri": getattr(mlflow_registry, "registry_uri", "N/A") if mlflow_registry.is_enabled() else "N/A",
        "experiment_name": getattr(mlflow_registry, "experiment_name", "N/A") if mlflow_registry.is_enabled() else "N/A",
        "experiment_id": getattr(mlflow_registry, "experiment_id", "N/A") if mlflow_registry.is_enabled() else "N/A",
    }


@app.get(f"{API_PREFIX}/mlflow/models")
async def list_mlflow_models():
    """
    Lista todos os modelos registrados no MLflow
    
    Returns:
        Lista de nomes de modelos
    """
    if not mlflow_registry or not mlflow_registry.is_enabled():
        raise HTTPException(status_code=503, detail="MLflow not enabled")
    
    models = mlflow_registry.list_models()
    return {"models": models, "count": len(models)}


@app.get(f"{API_PREFIX}/mlflow/models/{{model_name:path}}")
async def get_mlflow_model_info(model_name: str):
    """
    Obtém informações de um modelo específico
    
    Args:
        model_name: Nome do modelo
    
    Returns:
        Informações detalhadas do modelo
    """
    if not mlflow_registry or not mlflow_registry.is_enabled():
        raise HTTPException(status_code=503, detail="MLflow not enabled")
    
    info = mlflow_registry.get_model_info(model_name)
    if not info:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return info


@app.post(f"{API_PREFIX}/mlflow/models/{{model_name:path}}/transition")
async def transition_mlflow_model(model_name: str, version: str, stage: str):
    """
    Transiciona modelo para um stage
    
    Args:
        model_name: Nome do modelo
        version: Versão do modelo
        stage: Stage destino (Production, Staging, Archived)
    
    Returns:
        Confirmação da transição
    """
    if not mlflow_registry or not mlflow_registry.is_enabled():
        raise HTTPException(status_code=503, detail="MLflow not enabled")
    
    valid_stages = ["Production", "Staging", "Archived"]
    if stage not in valid_stages:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage. Must be one of: {valid_stages}"
        )
    
    success = mlflow_registry.transition_model_stage(model_name, version, stage)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to transition model")
    
    return {
        "model": model_name,
        "version": version,
        "stage": stage,
        "status": "transitioned"
    }


# Machine Learning Endpoints
@app.post(f"{API_PREFIX}/ml/predict-sinistrality")
async def predict_sinistrality_endpoint(features: Dict[str, Any]):
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


@app.post(f"{API_PREFIX}/ml/train-models")
async def train_ml_models_endpoint(data: Optional[List[Dict[str, Any]]] = None):
    """
    Treina os modelos de machine learning para predição de sinistralidade

    Args:
        data: Dados históricos opcionais para treinamento (se não fornecidos, usa dados sintéticos)

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


@app.get(f"{API_PREFIX}/ml/model-info")
async def get_ml_model_info_endpoint():
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


# External API Endpoints
@app.get(f"{API_PREFIX}/external/weather")
async def get_weather_endpoint(latitude: float, longitude: float):
    """
    Obter dados meteorológicos em tempo real

    Args:
        latitude: Latitude da localização
        longitude: Longitude da localização

    Returns:
        Dados meteorológicos atuais
    """
    try:
        result = await get_weather_data(latitude, longitude)
        return result
    except Exception as e:
        logger.error(f"Erro ao obter dados meteorológicos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro meteorológico: {str(e)}")


@app.get(f"{API_PREFIX}/external/economic-indicators")
async def get_economic_indicators_endpoint():
    """
    Obter indicadores econômicos atuais

    Returns:
        Taxa de inflação e crescimento do PIB
    """
    try:
        result = await get_economic_indicators()
        return result
    except Exception as e:
        logger.error(f"Erro ao obter indicadores econômicos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro econômico: {str(e)}")


@app.get(f"{API_PREFIX}/external/commodity-prices")
async def get_commodity_prices_endpoint(
    symbols: List[str] = Query(..., description="Símbolos das commodities")
):
    """
    Obter preços de commodities

    Args:
        symbols: Lista de símbolos de commodities

    Returns:
        Preços atuais das commodities
    """
    try:
        result = await get_commodity_prices(symbols)
        return result
    except Exception as e:
        logger.error(f"Erro ao obter preços de commodities: {e}")
        raise HTTPException(status_code=500, detail=f"Erro commodities: {str(e)}")


@app.get(f"{API_PREFIX}/external/real-time-data")
async def get_real_time_data_endpoint(
    latitude: float,
    longitude: float,
    commodities: List[str] = Query(
        ["CORN", "SOYBEAN"], description="Símbolos das commodities"
    ),
):
    """
    Obter dados abrangentes em tempo real de todas as APIs externas

    Args:
        latitude: Latitude da localização
        longitude: Longitude da localização
        commodities: Lista de símbolos de commodities

    Returns:
        Dados combinados de clima, economia e commodities
    """
    try:
        result = await get_real_time_data(latitude, longitude, commodities)

        # Registrar operação de auditoria
        log_operation(
            operation="external_data_retrieval",
            resource_type="external_api",
            action="fetch",
            status="success",
            resource_id=f"lat_{latitude}_lon_{longitude}",
            details={
                "latitude": latitude,
                "longitude": longitude,
                "commodities": commodities,
                "data_sources": ["weather", "economic", "commodity"],
            },
        )

        return result
    except Exception as e:
        # Registrar erro de auditoria
        log_operation(
            operation="external_data_retrieval",
            resource_type="external_api",
            action="fetch",
            status="error",
            resource_id=f"lat_{latitude}_lon_{longitude}",
            details={
                "error": str(e),
                "latitude": latitude,
                "longitude": longitude,
                "commodities": commodities,
            },
            compliance_flags=["external_api_error"],
        )
        logger.error(f"Erro ao obter dados em tempo real: {e}")
        raise HTTPException(status_code=500, detail=f"Erro dados tempo real: {str(e)}")


# Microsegmentation Endpoints
@app.post(f"{API_PREFIX}/microsegmentation/create")
async def create_microsegments_endpoint(
    region_bounds: Dict[str, Any],
    n_segments: int = Query(20, description="Número de microsegmentos"),
):
    """
    Criar microsegmentos para uma região geográfica

    Args:
        region_bounds: Limites e características da região
        n_segments: Número de microsegmentos a criar

    Returns:
        Definições dos microsegmentos criados
    """
    try:
        result = create_microsegments(region_bounds, n_segments)
        return result
    except Exception as e:
        logger.error(f"Erro ao criar microsegmentos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro microsegmentação: {str(e)}")


@app.get(f"{API_PREFIX}/microsegmentation/analyze-location")
async def analyze_location_risk_endpoint(
    latitude: float,
    longitude: float,
    region_id: str = Query("default", description="ID da região"),
):
    """
    Analisar risco de uma localização específica usando microsegmentação

    Args:
        latitude: Latitude da localização
        longitude: Longitude da localização
        region_id: ID da região para análise

    Returns:
        Análise de risco detalhada para a localização
    """
    try:
        result = analyze_location_risk(latitude, longitude, region_id)

        # Registrar operação de auditoria
        log_operation(
            operation="microsegmentation_analysis",
            resource_type="location_risk",
            action="analyze",
            status="success",
            resource_id=f"lat_{latitude}_lon_{longitude}",
            details={
                "latitude": latitude,
                "longitude": longitude,
                "region_id": region_id,
                "risk_score": result.get("risk_score", 0),
                "segment_id": result.get("segment_id"),
            },
            risk_score=result.get("risk_score", 0),
        )

        return result
    except Exception as e:
        # Registrar erro de auditoria
        log_operation(
            operation="microsegmentation_analysis",
            resource_type="location_risk",
            action="analyze",
            status="error",
            resource_id=f"lat_{latitude}_lon_{longitude}",
            details={"error": str(e), "latitude": latitude, "longitude": longitude},
            compliance_flags=["microsegmentation_error"],
        )
        logger.error(f"Erro ao analisar risco da localização: {e}")
        raise HTTPException(status_code=500, detail=f"Erro análise risco: {str(e)}")


@app.get(f"{API_PREFIX}/microsegmentation/summary")
async def get_microsegmentation_summary_endpoint(
    region_id: str = Query("default", description="ID da região")
):
    """
    Obter resumo estatístico da análise de microsegmentação

    Args:
        region_id: ID da região

    Returns:
        Estatísticas resumidas da microsegmentação
    """
    try:
        result = get_microsegmentation_summary(region_id)
        return result
    except Exception as e:
        logger.error(f"Erro ao obter resumo de microsegmentação: {e}")
        raise HTTPException(status_code=500, detail=f"Erro resumo: {str(e)}")


# Audit and Compliance Endpoints
@app.get(f"{API_PREFIX}/audit/logs")
async def get_audit_logs_endpoint(
    start_date: Optional[str] = Query(None, description="Data inicial (ISO format)"),
    end_date: Optional[str] = Query(None, description="Data final (ISO format)"),
    operation: Optional[str] = Query(None, description="Tipo de operação"),
    user_id: Optional[str] = Query(None, description="ID do usuário"),
    status: Optional[str] = Query(None, description="Status da operação"),
    limit: int = Query(100, description="Limite de registros"),
):
    """
    Obter logs de auditoria com filtros opcionais

    Returns:
        Lista de entradas do log de auditoria
    """
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        result = get_audit_logs(
            start_date=start,
            end_date=end,
            operation=operation,
            user_id=user_id,
            status=status,
            limit=limit,
        )
        return result
    except Exception as e:
        logger.error(f"Erro ao obter logs de auditoria: {e}")
        raise HTTPException(status_code=500, detail=f"Erro logs auditoria: {str(e)}")


@app.get(f"{API_PREFIX}/compliance/report")
async def get_compliance_report_endpoint(
    start_date: Optional[str] = Query(None, description="Data inicial (ISO format)"),
    end_date: Optional[str] = Query(None, description="Data final (ISO format)"),
):
    """
    Obter relatório de compliance

    Returns:
        Relatório de compliance com violações e estatísticas
    """
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None

        result = get_compliance_report(start_date=start, end_date=end)
        return result
    except Exception as e:
        logger.error(f"Erro ao obter relatório de compliance: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erro relatório compliance: {str(e)}"
        )


@app.post(f"{API_PREFIX}/audit/log-operation")
async def log_operation_endpoint(
    operation: str,
    resource_type: str,
    action: str,
    status: str = "success",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    risk_score: Optional[float] = None,
    compliance_flags: Optional[List[str]] = None,
):
    """
    Registrar uma operação para auditoria

    Returns:
        ID do registro de auditoria
    """
    try:
        audit_id = log_operation(
            operation=operation,
            resource_type=resource_type,
            action=action,
            status=status,
            user_id=user_id,
            session_id=session_id,
            resource_id=resource_id,
            details=details,
            risk_score=risk_score,
            compliance_flags=compliance_flags,
        )
        return {"audit_id": audit_id, "message": "Operação registrada com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao registrar operação: {e}")
        raise HTTPException(status_code=500, detail=f"Erro registro operação: {str(e)}")


# Pricing Endpoints
@app.post(f"{API_PREFIX}/pricing/calculate")
async def calculate_pricing_endpoint(request: PricingRequest):
    """
    Calcular preço de seguro baseado em dados climáticos e fatores de risco

    Args:
        request: Dados da solicitação de pricing

    Returns:
        Resultado do cálculo de pricing com recomendações
    """
    try:
        # Calcular pricing
        result = calculate_pricing(request)

        # Registrar operação de auditoria
        audit_id = log_operation(
            operation="pricing_calculation",
            resource_type="insurance_policy",
            action="calculate",
            status="success",
            user_id=request.user_id,
            session_id=request.session_id,
            resource_id=f"location_{request.location_id}",
            details={
                "location_id": request.location_id,
                "coverage_period": request.coverage_period,
                "coverage_amount": request.coverage_amount,
                "risk_factors": result.get("risk_factors", {}),
                "final_price": result.get("final_price", 0),
            },
            risk_score=result.get("risk_score", 0),
            compliance_flags=result.get("compliance_flags", []),
        )

        # Adicionar ID de auditoria ao resultado
        result["audit_id"] = audit_id

        return result
    except Exception as e:
        # Registrar erro de auditoria
        log_operation(
            operation="pricing_calculation",
            resource_type="insurance_policy",
            action="calculate",
            status="error",
            user_id=getattr(request, "user_id", None),
            session_id=getattr(request, "session_id", None),
            details={"error": str(e)},
            compliance_flags=["calculation_error"],
        )
        logger.error(f"Erro no cálculo de pricing: {e}")
        raise HTTPException(status_code=500, detail=f"Erro cálculo: {str(e)}")


# Função utilitária para cache com decorator
def cached_endpoint(ttl: int = 3600):
    """Decorator para endpoints com cache"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Gera chave baseada nos argumentos
            cache_key = smart_cache._generate_key(kwargs)
            cached_result = smart_cache.get(cache_key)

            if cached_result is not None:
                return cached_result

            # Executa a função se não estiver em cache
            result = await func(*args, **kwargs)

            # Armazena no cache
            smart_cache.set(cache_key, result, ttl)
            return result

        return wrapper

    return decorator


# Handler para erros HTTP
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.warning(f"HTTPException: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# Variável global para armazenar o health checker
health_checker: Optional[HealthChecker] = None


# Endpoint de verificação de saúde completa
@app.get(f"{API_PREFIX}/health/full")
async def health_check_full() -> Dict[str, Any]:
    """
    Verificação completa de saúde da API incluindo todas as dependências
    """
    if health_checker is None:
        return {
            "status": "degraded",
            "message": "Health checker não inicializado",
            "timestamp": time.time(),
        }

    return await health_checker.check_all()


# Endpoint de verificação de saúde crítica
@app.get(f"{API_PREFIX}/health/critical")
async def health_check_critical() -> Dict[str, Any]:
    """
    Verificação de saúde apenas de componentes críticos (Database, System)
    """
    if health_checker is None:
        return {"status": "degraded", "message": "Health checker não inicializado"}

    return await health_checker.check_critical()


# Endpoint de verificação de saúde simples (compatibilidade)
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Verificar o estado de saúde da API (health check simples)
    """
    status = "healthy" if not missing_vars else "degraded"
    response = {
        "status": status,
        "version": "1.0.0",
        "api_prefix": API_PREFIX,
    }

    if missing_vars:
        response["warnings"] = f"Configurações ausentes: {', '.join(missing_vars)}"
        response["missing_vars"] = missing_vars # Added this line based on the instruction's intent

    return response



# Verificar configuração antes de incluir os routers
# NOTE: Single unified startup event — see below at line ~1226


try:
    app.include_router(clima_router, prefix=f"{API_PREFIX}/clima", tags=["clima"])
    app.include_router(
        previsao_router, prefix=f"{API_PREFIX}/previsao", tags=["previsao"]
    )
    app.include_router(
        xweather_forecast_router,
        prefix=f"{API_PREFIX}/xweather",
        tags=["xweather-forecast"],
    )
    app.include_router(eventos_router, prefix=f"{API_PREFIX}/eventos", tags=["eventos"])
    app.include_router(
        tokenizacao_router, prefix=f"{API_PREFIX}/tokenizacao", tags=["tokenizacao"]
    )
    app.include_router(
        blockchain_tokens_router, prefix=f"{API_PREFIX}/blockchain", tags=["blockchain"]
    )
    app.include_router(
        modelagem_router, prefix=f"{API_PREFIX}/modelagem", tags=["modelagem"]
    )
    app.include_router(alertas_router, prefix=f"{API_PREFIX}/alertas", tags=["alertas"])
    app.include_router(
        localizacao_router, prefix=f"{API_PREFIX}/localizacao", tags=["localizacao"]
    )
    app.include_router(auth_router, prefix=f"{API_PREFIX}/auth", tags=["auth"])
    app.include_router(
        mathematical_engines_router,
        prefix=f"{API_PREFIX}/math-engines",
        tags=["mathematical-engines"],
    )
    app.include_router(
        climate_risk_modeling_router,
        prefix=f"{API_PREFIX}/climate-risk",
        tags=["climate-risk-modeling"],
    )
    if lstm_attention_router:
        app.include_router(
            lstm_attention_router,
            prefix=f"{API_PREFIX}/lstm-attention",
            tags=["lstm-attention"],
        )
    app.include_router(parametric_router, prefix=f"{API_PREFIX}")
    app.include_router(transparency_router, prefix=f"{API_PREFIX}")
    app.include_router(carbon_router, prefix=f"{API_PREFIX}")
    try:
        from api.oracle import router as oracle_router
        app.include_router(oracle_router, prefix=f"{API_PREFIX}")
    except Exception as e:
        logger.warning(f"Oracle router not loaded: {e}")
    app.include_router(
        parametric_insurance_router,
        prefix=f"{API_PREFIX}/parametric-insurance",
        tags=["parametric-insurance"],
    )
    app.include_router(
        climate_hmm_router, prefix=f"{API_PREFIX}/climate-hmm", tags=["climate-hmm"]
    )
    app.include_router(
        ensemble_pricing_router,
        prefix=f"{API_PREFIX}/ensemble-pricing",
        tags=["ensemble-pricing"],
    )
    app.include_router(
        extreme_value_pricing_router,
        prefix=f"{API_PREFIX}/pricing/extreme-value",
        tags=["extreme-value-pricing"],
    )
    app.include_router(
        climate_risk_analysis_router,
        prefix=f"{API_PREFIX}/climate-risk-analysis",
        tags=["climate-risk-analysis"],
    )
    app.include_router(
        climate_premium_router,
        prefix=f"{API_PREFIX}/climate-premium",
        tags=["climate-premium"],
    )
    app.include_router(
        bayesian_bootstrap_router,
        prefix=f"{API_PREFIX}/bayesian-bootstrap",
        tags=["bayesian-bootstrap"],
    )
    app.include_router(
        climate_alert_router,
        prefix=f"{API_PREFIX}/climate-alert",
        tags=["climate-alert"],
    )
    app.include_router(
        performance_testing_router,
        prefix=f"{API_PREFIX}/performance-testing",
        tags=["performance-testing"],
    )
    if dynamical_climate_router:
        app.include_router(
            dynamical_climate_router,
            prefix=f"{API_PREFIX}/dynamical-climate",
            tags=["dynamical-climate"],
        )
    app.include_router(
        dynamic_insurance_analysis_router,
        prefix=f"{API_PREFIX}/dynamic-insurance",
        tags=["dynamic-insurance"],
    )
    app.include_router(
        integrated_pipeline_router,
        prefix=f"{API_PREFIX}/integrated-pipeline",
        tags=["integrated-pipeline"],
    )
    app.include_router(
        physical_risk_router,
        prefix=f"{API_PREFIX}/physical-risk",
        tags=["physical-risk"],
    )
    app.include_router(
        transition_risk_router,
        prefix=f"{API_PREFIX}/transition-risk",
        tags=["transition-risk"],
    )
    app.include_router(
        concentration_risk_router,
        prefix=f"{API_PREFIX}/concentration-risk",
        tags=["concentration-risk"],
    )
    app.include_router(
        mitigation_measures_router,
        prefix=f"{API_PREFIX}/mitigation-measures",
        tags=["mitigation-measures"],
    )
    app.include_router(
        lei_analysis_router, prefix=f"{API_PREFIX}/lei-analysis", tags=["lei-analysis"]
    )
    app.include_router(
        operating_costs_router,
        prefix=f"{API_PREFIX}/operating-costs",
        tags=["operating-costs"],
    )
    app.include_router(
        climate_capital_charge_router,
        prefix=f"{API_PREFIX}/climate-capital-charge",
        tags=["climate-capital-charge"],
    )
    app.include_router(
        loading_margin_router,
        prefix=f"{API_PREFIX}/loading-margin",
        tags=["loading-margin"],
    )
    app.include_router(
        investment_return_router,
        prefix=f"{API_PREFIX}/investment-return",
        tags=["investment-return"],
    )
    app.include_router(
        comprehensive_pricing_router,
        prefix=f"{API_PREFIX}/comprehensive-pricing",
        tags=["comprehensive-pricing"],
    )
    app.include_router(
        integrated_pricing_framework_router,
        prefix=f"{API_PREFIX}/integrated-pricing-framework",
        tags=["integrated-pricing-framework"],
    )
    app.include_router(
        climate_risk_report_router,
        prefix=f"{API_PREFIX}/climate-risk-report",
        tags=["climate-risk-report"],
    )
    app.include_router(
        tcfd_issb_router, prefix=f"{API_PREFIX}/tcfd-issb", tags=["tcfd-issb"]
    )
    app.include_router(
        climate_scr_router, prefix=f"{API_PREFIX}/climate-scr", tags=["climate-scr"]
    )
    app.include_router(
        policy_uncertainty_router,
        prefix=f"{API_PREFIX}/policy-uncertainty",
        tags=["policy-uncertainty"],
    )
    app.include_router(
        smart_exclusions_router,
        prefix=f"{API_PREFIX}/smart-exclusions",
        tags=["smart-exclusions"],
    )
    app.include_router(
        sips_performance_analytics_router,
        prefix=f"{API_PREFIX}/sips-analytics",
        tags=["sips-analytics"],
    )
    app.include_router(
        ia_analytics_agent_router, prefix=f"{API_PREFIX}/ia-agent", tags=["ia-agent"]
    )
    app.include_router(
        gemini_integration_router, prefix=f"{API_PREFIX}/gemini", tags=["gemini"]
    )
    app.include_router(
        grok_integration_router, prefix=f"{API_PREFIX}/grok", tags=["grok"]
    )
    app.include_router(
        noaa_integration_router, prefix=f"{API_PREFIX}/noaa", tags=["noaa"]
    )
    app.include_router(
        xweather_forecast_router, prefix=f"{API_PREFIX}/xweather", tags=["xweather"]
    )
    app.include_router(
        model_governance_router, prefix=f"{API_PREFIX}/model-governance", tags=["model-governance"]
    )
    app.include_router(
        regulatory_reporting_router, prefix=f"{API_PREFIX}/regulatory-reporting", tags=["regulatory-reporting"]
    )
    app.include_router(
        inmet_alertas_router, prefix=f"{API_PREFIX}/inmet-alertas", tags=["inmet-alertas"]
    )
    app.include_router(
        brazil_disaster_alerts_router, prefix=f"{API_PREFIX}/brazil-alerts", tags=["brazil-alerts"]
    )
    app.include_router(
        parametric_trigger_router, prefix=f"{API_PREFIX}/parametric-triggers", tags=["parametric-triggers"]
    )
    app.include_router(
        policy_valuation_router,
        prefix=f"{API_PREFIX}/policy-valuation",
        tags=["policy-valuation"],
    )
    app.include_router(
        policy_pricing_router,
        prefix=f"{API_PREFIX}/policy-pricing",
        tags=["policy-pricing"],
    )
    app.include_router(
        policy_risk_monitor_router,
        prefix=f"{API_PREFIX}/risk-monitor",
        tags=["risk-monitor"],
    )
    app.include_router(
        probabilistic_climate_scenarios_router,
        prefix=f"{API_PREFIX}/probabilistic-climate-scenarios",
        tags=["probabilistic-climate-scenarios"],
    )
    app.include_router(i18n_router, prefix=f"{API_PREFIX}/i18n", tags=["i18n"])
    app.include_router(
        english_api_router, prefix=f"{API_PREFIX}/english", tags=["english"]
    )
    app.include_router(
        english_climateai_router,
        prefix=f"{API_PREFIX}/english-climateai",
        tags=["english-climateai"],
    )
    # New refactored routers
    app.include_router(cache_router, prefix=f"{API_PREFIX}/cache", tags=["cache"])
    if ml_router:
        app.include_router(ml_router, prefix=f"{API_PREFIX}/ml", tags=["ml"])
    app.include_router(
        external_router, prefix=f"{API_PREFIX}/external", tags=["external"]
    )
    app.include_router(
        microsegmentation_router,
        prefix=f"{API_PREFIX}/microsegmentation",
        tags=["microsegmentation"],
    )
    app.include_router(pricing_router, prefix=f"{API_PREFIX}/pricing", tags=["pricing"])
    app.include_router(
        unified_pricing_router,
        prefix=f"{API_PREFIX}/unified-pricing",
        tags=["unified-pricing"],
    )
    # Tier 1 Regulatory Compliance
    app.include_router(
        backtesting_router, prefix=f"{API_PREFIX}", tags=["backtesting"]
    )
    app.include_router(
        audit_router, prefix=f"{API_PREFIX}/audit", tags=["audit"]
    )
    # app.include_router(audit_router, prefix=f"{API_PREFIX}/audit", tags=["audit"])
except Exception as e:
    logger.error(f"Erro ao incluir routers: {str(e)}")
    raise


# Eventos de startup e shutdown
@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização do servidor"""
    global health_checker

    logger.info("Inicializando ClimateAI...")

    # Verificar variáveis de ambiente críticas
    if missing_vars:
        logger.warning(
            "Servidor iniciado com configurações incompletas. "
            f"Variáveis ausentes: {', '.join(missing_vars)}"
        )

    # Inicializar banco de dados
    if settings.DATABASE_ENABLED:
        await init_db()
        logger.info("Banco de dados inicializado")

    # Inicializar o health checker
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            database_url = "sqlite:///./test.db"

        redis_url = os.getenv("REDIS_URL", None)
        health_checker = HealthChecker(database_url=database_url, redis_url=redis_url)
        logger.info("✓ Health checker inicializado com sucesso")
    except Exception as e:
        logger.warning(f"⚠ Falha ao inicializar health checker: {str(e)}")
        health_checker = None

    # Log de status dos serviços Tier 1
    logger.info("=" * 60)
    logger.info("STATUS DOS SERVIÇOS TIER 1:")
    logger.info("=" * 60)
    
    if vault_manager and vault_manager.is_enabled():
        logger.info(f"✓ Vault Secrets Manager: {vault_manager.url}")
    else:
        logger.warning("⚠ Vault Secrets Manager: Não configurado")
    
    if mlflow_registry and mlflow_registry.is_enabled():
        logger.info(f"✓ MLflow Model Registry: {mlflow_registry.tracking_uri}")
    else:
        logger.warning("⚠ MLflow Model Registry: Não configurado")
    
    logger.info("=" * 60)
    logger.info("Servidor ClimateAI iniciado com sucesso")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no encerramento do servidor"""
    logger.info("Encerrando ClimateAI...")
    if settings.DATABASE_ENABLED:
        await close_db()
        logger.info("Conexões de banco de dados fechadas")


@app.get("/")
async def root():
    return {"message": "Framework Integrado de Modelagem Climático-Econômica (FIMCE)"}


if __name__ == "__main__":
    logger.info("Iniciando servidor FIMCE...")
    uvicorn.run(
        "main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG
    )
