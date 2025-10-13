"""
Framework Integrado de Modelagem Climático-Econômica (FIMCE)
Servidor principal do sistema de previsão climática e modelagem de preços
"""
import os
import logging
import time
import hashlib
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import uvicorn
from functools import lru_cache

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
            key for key, timestamp in self.cache_timestamps.items()
            if current_time - timestamp >= self.max_age
        ]
        for key in expired_keys:
            del self.cache[key]
            del self.cache_timestamps[key]
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")

# Instância global do cache
smart_cache = SmartCache()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar routers e configurações
from api.clima import router as clima_router
from api.previsao import router as previsao_router
from api.eventos import router as eventos_router
from api.modelagem import router as modelagem_router
from api.alertas import router as alertas_router
from api.localizacao import router as localizacao_router
from api.auth import router as auth_router
# from api.audit import router as audit_router
from services.ml_service import predict_sinistrality, train_ml_models, get_ml_model_info
from services.external_api_service import get_weather_data, get_economic_indicators, get_commodity_prices, get_real_time_data
from services.microsegmentation_service import create_microsegments, analyze_location_risk, get_microsegmentation_summary
from services.audit_service import log_operation, log_risk_assessment, log_policy_decision, get_audit_logs, get_compliance_report
from config.config import settings
from config.database import init_db, close_db

# Importar Pydantic models para pricing
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import Query

class PricingRequest(BaseModel):
    location_id: str
    coverage_amount: float
    coverage_period: int = 1  # em anos
    user_id: Optional[str] = None
    session_id: Optional[str] = None

# Função de cálculo de pricing (placeholder - implementar lógica completa)
def calculate_pricing(request: PricingRequest) -> Dict[str, Any]:
    """
    Calcula preço de seguro baseado em dados climáticos e fatores de risco
    """
    # Placeholder - implementar lógica real de cálculo
    # Por enquanto retorna dados simulados
    return {
        "final_price": request.coverage_amount * 0.05,  # 5% do valor coberto
        "risk_score": 0.3,
        "risk_factors": {
            "climatic_risk": 0.4,
            "economic_risk": 0.2,
            "location_risk": 0.3
        },
        "recommendations": [
            "Considerar cobertura adicional contra inundações",
            "Avaliar período de cobertura mais longo"
        ],
        "compliance_flags": []
    }

# Verificar variáveis de ambiente críticas
required_env_vars = [
    ('EMBRAPA_API_KEY', 'Chave da API da Embrapa'),
    ('EMBRAPA_API_URL', 'URL da API da Embrapa'),
    ('EMBRAPA_API_VERSION', 'Versão da API da Embrapa')
]

missing_vars = []
for var, description in required_env_vars:
    if not os.getenv(var):
        missing_vars.append(f"{description} ({var})")
        logger.warning(f"Variável de ambiente não encontrada: {var}")

# Criar a aplicação FastAPI com gestão de erros melhorada
app = FastAPI(
    title="FIMCE API",
    description="API do Framework Integrado de Modelagem Climático-Econômica",
    version="1.0.0"
)

API_PREFIX = "/api/v1"

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adicionar middleware de autenticação opcional
from middleware.auth_middleware import optional_auth
app.middleware("http")(optional_auth)

# Middleware de cache
@app.middleware("http")
async def cache_middleware(request: Request, call_next):
    # Limpa entradas expiradas periodicamente
    smart_cache.clear_expired()

    response = await call_next(request)
    return response

# Handler para erros genéricos
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Erro não tratado: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor", "message": str(exc)}
    )

# Endpoint para estatísticas do cache
@app.get("/api/v1/cache/stats")
async def get_cache_stats():
    """Retorna estatísticas do sistema de cache"""
    return {
        "total_entries": len(smart_cache.cache),
        "cache_size_mb": len(str(smart_cache.cache)) / (1024 * 1024),  # Aproximação
        "max_age_seconds": smart_cache.max_age,
        "uptime": "Sistema ativo"
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
            details={
                "features": features,
                "predictions": result
            },
            risk_score=result.get("risk_score", 0)
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
            compliance_flags=["ml_prediction_error"]
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
async def get_commodity_prices_endpoint(symbols: List[str] = Query(..., description="Símbolos das commodities")):
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
    commodities: List[str] = Query(['CORN', 'SOYBEAN'], description="Símbolos das commodities")
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
                "data_sources": ["weather", "economic", "commodity"]
            }
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
            details={"error": str(e), "latitude": latitude, "longitude": longitude, "commodities": commodities},
            compliance_flags=["external_api_error"]
        )
        logger.error(f"Erro ao obter dados em tempo real: {e}")
        raise HTTPException(status_code=500, detail=f"Erro dados tempo real: {str(e)}")

# Microsegmentation Endpoints
@app.post("/api/v1/microsegmentation/create")
async def create_microsegments_endpoint(region_bounds: Dict[str, Any], n_segments: int = Query(20, description="Número de microsegmentos")):
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
    region_id: str = Query('default', description="ID da região")
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
                "segment_id": result.get("segment_id")
            },
            risk_score=result.get("risk_score", 0)
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
            compliance_flags=["microsegmentation_error"]
        )
        logger.error(f"Erro ao analisar risco da localização: {e}")
        raise HTTPException(status_code=500, detail=f"Erro análise risco: {str(e)}")

@app.get("/api/v1/microsegmentation/summary")
async def get_microsegmentation_summary_endpoint(region_id: str = Query('default', description="ID da região")):
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
    limit: int = Query(100, description="Limite de registros")
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
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Erro ao obter logs de auditoria: {e}")
        raise HTTPException(status_code=500, detail=f"Erro logs auditoria: {str(e)}")

@app.get("/api/v1/compliance/report")
async def get_compliance_report_endpoint(
    start_date: Optional[str] = Query(None, description="Data inicial (ISO format)"),
    end_date: Optional[str] = Query(None, description="Data final (ISO format)")
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
        raise HTTPException(status_code=500, detail=f"Erro relatório compliance: {str(e)}")

@app.post("/api/v1/audit/log-operation")
async def log_operation_endpoint(
    operation: str,
    resource_type: str,
    action: str,
    status: str = 'success',
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    risk_score: Optional[float] = None,
    compliance_flags: Optional[List[str]] = None
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
            compliance_flags=compliance_flags
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
                "final_price": result.get("final_price", 0)
            },
            risk_score=result.get("risk_score", 0),
            compliance_flags=result.get("compliance_flags", [])
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
            user_id=getattr(request, 'user_id', None),
            session_id=getattr(request, 'session_id', None),
            details={"error": str(e)},
            compliance_flags=["calculation_error"]
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
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Endpoint de verificação de saúde
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Verificar o estado de saúde da API e suas dependências
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

try:
    app.include_router(clima_router, prefix=f"{API_PREFIX}/clima", tags=["clima"])
    app.include_router(previsao_router, prefix=f"{API_PREFIX}/previsao", tags=["previsao"])
    app.include_router(eventos_router, prefix=f"{API_PREFIX}/eventos", tags=["eventos"])
    app.include_router(modelagem_router, prefix=f"{API_PREFIX}/modelagem", tags=["modelagem"])
    app.include_router(alertas_router, prefix=f"{API_PREFIX}/alertas", tags=["alertas"])
    app.include_router(localizacao_router, prefix=f"{API_PREFIX}/localizacao", tags=["localizacao"])
    app.include_router(auth_router, prefix=f"{API_PREFIX}/auth", tags=["auth"])
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
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
