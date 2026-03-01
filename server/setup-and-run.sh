#!/bin/bash
# Instalação e inicialização rápida do ClimateWise Backend

echo "=== ClimateWise Backend Setup ==="
echo ""

cd /home/exp/Downloads/ClimateAI/server

# Criar venv se não existir
if [ ! -d "venv-hathor" ]; then
  echo "Criando virtual environment..."
  python3 -m venv venv-hathor
fi

source venv-hathor/bin/activate

# Instalar dependências essenciais
echo "Instalando dependências..."
pip install -q \
  fastapi uvicorn pydantic pydantic-settings \
  python-json-logger PyJWT python-jose \
  requests httpx aiohttp \
  redis sqlalchemy aiosqlite \
  passlib bcrypt \
  numpy pandas \
  python-multipart python-dotenv \
  scipy scikit-learn 2>&1 | tail -3

# Configurar ambiente
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export DATABASE_ENABLED=false
export SECRET_KEY="dev-secret-key-for-testing"
export DEBUG=true

# Matar processos antigos
pkill -9 -f "uvicorn.*main" 2>/dev/null
sleep 2

# Iniciar servidor
echo "Iniciando backend na porta 8000..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Aguardar inicialização
echo "Aguardando servidor..."
for i in {1..60}; do
  if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo ""
    echo "✅ Backend ONLINE!"
    echo ""
    echo "Acessos:"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - Hathor API: http://localhost:8000/api/v1/blockchain/hathor"
    echo "  - Oracle: http://localhost:8000/api/v1/blockchain/hathor/oracle/index"
    echo ""
    echo "PID: $SERVER_PID"
    exit 0
  fi
  echo -n "."
  sleep 1
done

echo ""
echo "❌ Servidor falhou ao iniciar"
exit 1
