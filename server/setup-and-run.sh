#!/bin/bash
# Instalação e inicialização rápida do ClimateWise Backend

echo "=== ClimateWise Backend Setup ==="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -x "$SCRIPT_DIR/../.venv/bin/python" ]; then
  VENV_PYTHON="$SCRIPT_DIR/../.venv/bin/python"
else
  VENV_DIR="$SCRIPT_DIR/venv-hathor"
  VENV_PYTHON="$VENV_DIR/bin/python3"

  # Criar venv se não existir
  if [ ! -d "$VENV_DIR" ]; then
    echo "Criando virtual environment..."
    python3 -m venv "$VENV_DIR"
  fi
fi

if [ ! -x "$VENV_PYTHON" ]; then
  echo "❌ Python do virtual environment não encontrado em $VENV_PYTHON"
  exit 1
fi

# Instalar dependências essenciais
echo "Instalando dependências..."
"$VENV_PYTHON" -m pip install -q \
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
export SECRET_KEY="${SECRET_KEY:-$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)}"
export DEBUG=true

# Matar processos antigos
pkill -9 -f "uvicorn.*main" 2>/dev/null
sleep 2

# Iniciar servidor
echo "Iniciando backend na porta 8000..."
"$VENV_PYTHON" -m uvicorn main:app --host 0.0.0.0 --port 8000 &
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
