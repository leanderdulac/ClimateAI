"""
Framework Integrado de Modelagem Climático-Econômica (FIMCE)
Servidor principal do sistema de previsão climática e modelagem de preços
"""

import hashlib
import logging
import os
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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


# Sistema de Cache Inteligente
class SmartCache:
    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.max_age = 3600  # 1 hora por padrão

    def _generate_key(self, data: Any) -> str:
        """Gera uma chave única para os dados"""
        if isinstance(data, dict):
            # Ordena as chaves para consistência
            sorted_data = str(sorted(data.items()))
        else:
            sorted_data = str(data)
        return hashlib.md5(sorted_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Recupera dados do cache se ainda válidos"""
        if key in self.cache:
            timestamp = self.cache_timestamps.get(key, 0)
            if time.time() - timestamp < self.max_age:
                logger.info(f"Cache hit for key: {key[:8]}...")
                return self.cache[key]
            else:
                # Remove entrada expirada
                del self.cache[key]
                del self.cache_timestamps[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Armazena dados no cache"""
        self.cache[key] = value
        self.cache_timestamps[key] = time.time()
        if ttl:
            self.max_age = ttl
        logger.info(f"Cached data for key: {key[:8]}...")

    def clear_expired(self) -> None:
        """Remove entradas expiradas do cache"""
        current_time = time.time()
        expired_keys = [
            key
            for key, timestamp in self.cache_timestamps.items()
            if current_time - timestamp >= self.max_age
        ]
        for key in expired_keys:
            del self.cache[key]
            del self.cache_timestamps[key]
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
from api.bayesian_bootstrap import router as bayesian_bootstrap_router
from api.blockchain_tokens import router as blockchain_tokens_router

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
from api.dynamical_climate import router as dynamical_climate_router
from api.english_api import router as english_api_router
from api.english_climateai import router as english_climateai_router
from api.ensemble_pricing import router as ensemble_pricing_router
from api.eventos import router as eventos_router
from api.gemini_integration import router as gemini_integration_router
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
from api.lstm_attention import router as lstm_attention_router
from api.mathematical_engines import router as mathematical_engines_router
from api.mitigation_measures import router as mitigation_measures_router
from api.modelagem import router as modelagem_router
from api.operating_costs import router as operating_costs_router
from api.parametric_insurance import router as parametric_insurance_router
from api.performance_testing import router as performance_testing_router
from api.physical_risk import router as physical_risk_router
from api.policy_pricing import router as policy_pricing_router
from api.policy_uncertainty import router as policy_uncertainty_router
from api.policy_valuation import router as policy_valuation_router
from api.previsao import router as previsao_router
from api.sips_performance_analytics import router as sips_performance_analytics_router
from api.smart_exclusions import router as smart_exclusions_router
from api.tcfd_issb import router as tcfd_issb_router
from api.tokenizacao import router as tokenizacao_router
from api.transition_risk import router as transition_risk_router
from config.config import settings
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
from services.ml_service import (
    get_ml_model_info,
    predict_sinistrality,
    sinistrality_predictor,
    train_ml_models,
)


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
from lib.exception_handlers import register_handlers

# (Código omitido para brevidade)

# Criar a aplicação FastAPI com gestão de erros melhorada
app = FastAPI(
    title="FIMCE API",
    description="API do Framework Integrado de Modelagem Climático-Econômica",
    version="1.0.0",
)

# Registrar os handlers de exceção customizados
register_handlers(app)

API_PREFIX = "/api/v1"

# (Restante do código, incluindo middlewares e routers)


# Endpoint para estatísticas do cache
@app.get("/api/v1/cache/stats")
async def get_cache_stats():
    """Retorna estatísticas do sistema de cache"""
    return {
        "total_entries": len(smart_cache.cache),
        "cache_size_mb": len(str(smart_cache.cache)) / (1024 * 1024),  # Aproximação
        "max_age_seconds": smart_cache.max_age,
        "uptime": "Sistema ativo",
    }


@app.post("/api/v1/cache/clear")
async def clear_cache():
    """Limpa todo o cache"""
    smart_cache.cache.clear()
    smart_cache.cache_timestamps.clear()
    return {"message": "Cache limpo com sucesso"}


# Machine Learning Endpoints
@app.post("/api/v1/ml/predict-sinistrality")
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


@app.post("/api/v1/ml/train-models")
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


@app.get("/api/v1/ml/model-info")
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
@app.get("/api/v1/external/weather")
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


@app.get("/api/v1/external/economic-indicators")
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


@app.get("/api/v1/external/commodity-prices")
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


@app.get("/api/v1/external/real-time-data")
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
@app.post("/api/v1/microsegmentation/create")
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


@app.get("/api/v1/microsegmentation/analyze-location")
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


@app.get("/api/v1/microsegmentation/summary")
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
@app.get("/api/v1/audit/logs")
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


@app.get("/api/v1/compliance/report")
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


@app.post("/api/v1/audit/log-operation")
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
@app.post("/api/v1/pricing/calculate")
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
@app.get("/api/v1/health/full")
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
@app.get("/api/v1/health/critical")
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
    }

    if missing_vars:
        response["warnings"] = f"Configurações ausentes: {', '.join(missing_vars)}"

    return response


# Verificar configuração antes de incluir os routers
@app.on_event("startup")
async def startup_event():
    """
    Verificar configurações e dependências na inicialização
    """
    global health_checker

    logger.info("Iniciando servidor FIMCE...")

    # Verificar variáveis de ambiente críticas
    if missing_vars:
        logger.warning(
            "Servidor iniciado com configurações incompletas. "
            f"Variáveis ausentes: {', '.join(missing_vars)}"
        )

    # Verificar configurações do settings
    try:
        # No Pydantic v2, a validação é automática na criação da instância
        logger.info("Configurações validadas com sucesso")
    except Exception as e:
        logger.error(f"Erro na validação das configurações: {str(e)}")
        raise

    # Inicializar o health checker
    try:
        # Obter URL do banco de dados
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            # Usar SQLite como fallback
            database_url = "sqlite:///./test.db"

        # Obter URL do Redis (opcional)
        redis_url = os.getenv("REDIS_URL", None)

        # Criar instância global do health checker
        health_checker = HealthChecker(database_url=database_url, redis_url=redis_url)

        logger.info("Health checker inicializado com sucesso")
        logger.info(f"Database URL configurada: {database_url[:50]}...")
        if redis_url:
            logger.info(f"Redis URL configurada: {redis_url[:50]}...")
        else:
            logger.info("Redis não configurado (verificações de cache desabilitadas)")

    except Exception as e:
        logger.warning(f"Falha ao inicializar health checker: {str(e)}")
        # Não falhar completamente se o health checker não inicializar
        health_checker = None


try:
    app.include_router(clima_router, prefix=f"{API_PREFIX}/clima", tags=["clima"])
    app.include_router(
        previsao_router, prefix=f"{API_PREFIX}/previsao", tags=["previsao"]
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
    app.include_router(
        lstm_attention_router,
        prefix=f"{API_PREFIX}/lstm-attention",
        tags=["lstm-attention"],
    )
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
        policy_valuation_router,
        prefix=f"{API_PREFIX}/policy-valuation",
        tags=["policy-valuation"],
    )
    app.include_router(
        policy_pricing_router,
        prefix=f"{API_PREFIX}/policy-pricing",
        tags=["policy-pricing"],
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
    # app.include_router(audit_router, prefix=f"{API_PREFIX}/audit", tags=["audit"])
except Exception as e:
    logger.error(f"Erro ao incluir routers: {str(e)}")
    raise


# Eventos de startup e shutdown
@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização do servidor"""
    logger.info("Inicializando ClimateAI...")
    if settings.DATABASE_ENABLED:
        await init_db()
        logger.info("Banco de dados inicializado")
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
