#!/usr/bin/env python3
"""
Minimal Hathor Blockchain API Server
Servidor mínimo apenas para testar a API Hathor sem dependências do main.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import apenas do router Hathor
from api.hathor_blockchain import router as hathor_router

app = FastAPI(
    title="ClimateWise - Hathor Blockchain API",
    description="API para tokenização de índices climáticos na Hathor Network",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers - sem prefix duplicado
app.include_router(hathor_router, tags=["Hathor Blockchain"])

@app.get("/")
def root():
    return {
        "message": "ClimateWise Hathor Blockchain API",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
