"""
Framework Integrado de Modelagem Climático-Econômica (FIMCE)
Servidor principal do sistema de previsão climática e modelagem de preços
"""
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import uvicorn

from api.clima import router as clima_router
from api.previsao import router as previsao_router
from api.eventos import router as eventos_router
from api.modelagem import router as modelagem_router
from api.alertas import router as alertas_router
from config.config import settings

app = FastAPI(
    title="Framework Integrado de Modelagem Climático-Econômica (FIMCE)",
    description="Sistema avançado para previsão climática e modelagem de preços",
    version="1.0.0"
)

# Configuração de CORS para permitir comunicação com o frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substituir por domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluindo os routers
app.include_router(clima_router, prefix="/api/v1", tags=["clima"])
app.include_router(previsao_router, prefix="/api/v1", tags=["previsao"])
app.include_router(eventos_router, prefix="/api/v1", tags=["eventos"])
app.include_router(modelagem_router, prefix="/api/v1", tags=["modelagem"])
app.include_router(alertas_router, prefix="/api/v1", tags=["alertas"])

@app.get("/")
async def root():
    return {"message": "Framework Integrado de Modelagem Climático-Econômica (FIMCE)"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "FIMCE API"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )