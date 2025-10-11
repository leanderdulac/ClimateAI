"""
Framework Integrado de Modelagem Climático-Econômica (FIMCE)
Servidor principal do sistema de previsão climática e modelagem de preços
"""
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict
import uvicorn

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
from config.config import settings

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

# Handler para erros genéricos
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Erro não tratado: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor", "message": str(exc)}
    )

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
except Exception as e:
    logger.error(f"Erro ao incluir routers: {str(e)}")
    raise

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
