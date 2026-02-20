"""
ClimateAI - Servidor Demo Simplificado
Para demonstração das funcionalidades Tier 1
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid

app = FastAPI(title="ClimateAI Demo", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware X-Request-ID
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration:.3f}s"
    
    return response

@app.get("/")
async def root():
    return {
        "message": "ClimateAI API - Tier 1 Demo",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "climateai-backend",
        "timestamp": time.time(),
        "checks": {
            "api": "ok",
            "database": "mock_ok",
            "redis": "mock_ok"
        }
    }

@app.get("/api/v1/test")
async def test_endpoint(request: Request):
    return {
        "message": "Test endpoint working",
        "request_id": request.state.request_id,
        "timestamp": time.time()
    }

@app.get("/api/v1/policy_pricing/mock")
async def mock_pricing():
    return {
        "is_approved": True,
        "status": "APPROVED",
        "financials": {
            "pure_premium": 1100.0,
            "total_premium": 1485.0,
            "net_profit": 74.25,
            "profit_margin_pct": 5.0,
            "combined_ratio": 95.0
        },
        "decision_flow": "MOCK_CALCULATED"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
