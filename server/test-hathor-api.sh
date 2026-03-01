#!/bin/bash
# Teste Rápido da API Hathor - Sem banco de dados

cd /home/exp/Downloads/ClimateAI/server
source venv-hathor/bin/activate

# Matar processos existentes
pkill -9 -f uvicorn 2>/dev/null
sleep 2

# Criar app mínimo só para testar Hathor
cat > /tmp/test_hathor_app.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.hathor_blockchain import router as hathor_router

app = FastAPI(title="Hathor Blockchain Test")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(hathor_router, prefix="/api/v1/blockchain/hathor", tags=["Hathor"])

@app.get("/")
def root():
    return {"message": "Hathor Blockchain API Test", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}
EOF

# Iniciar app mínimo
echo "Iniciando API Hathor mínima..."
echo "Acesse: http://localhost:8002/docs"
echo ""

python3 -m uvicorn /tmp/test_hathor_app:app --host 0.0.0.0 --port 8002 --reload &
APP_PID=$!

# Aguardar início
sleep 10

# Testar
echo "Testando endpoints..."
curl -s http://localhost:8002/health
echo ""
curl -s http://localhost:8002/api/v1/blockchain/hathor/tokens
echo ""

echo ""
echo "API rodando no PID: $APP_PID"
echo "Docs: http://localhost:8002/docs"
echo "Para parar: kill $APP_PID"
