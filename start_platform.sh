#!/bin/bash

# Script para iniciar toda a plataforma ClimateWise

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PYTHONPATH="$PROJECT_ROOT/server:$PROJECT_ROOT"

echo "🚀 Iniciando Plataforma ClimateWise..."

# Função para verificar se uma porta está livre
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Porta $port já está em uso"
        return 1
    else
        echo "✅ Porta $port está livre"
        return 0
    fi
}

wait_for_http() {
    local name=$1
    local url=$2
    local max_attempts=${3:-30}
    local attempt=1

    while [ "$attempt" -le "$max_attempts" ]; do
        if curl -fsS "$url" >/dev/null 2>&1; then
            echo "✅ $name pronto"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done

    echo "❌ $name não respondeu a tempo"
    return 1
}

# Require project .venv (never fall back to committed server/venv-hathor)
VENV_BIN="$PROJECT_ROOT/.venv/bin/python"
if [ ! -x "$VENV_BIN" ]; then
    echo "ERROR: .venv not found at $PROJECT_ROOT/.venv"
    echo "Create with: python3 -m venv .venv && pip install -r server/requirements-prod-ml.txt"
    exit 1
fi

# Verificar portas
echo "📊 Verificando portas..."
check_port 8000 && BACKEND_OK=true || BACKEND_OK=false
check_port 5173 && FRONTEND_OK=true || FRONTEND_OK=false

# Iniciar backend
if [ "$BACKEND_OK" = true ]; then
    echo "🔧 Iniciando Backend (porta 8000)..."
    (
        cd "$PROJECT_ROOT/server"
        source "$PROJECT_ROOT/.venv/bin/activate"
        export PYTHONPATH="$BACKEND_PYTHONPATH${PYTHONPATH:+:$PYTHONPATH}"
        "$PROJECT_ROOT/.venv/bin/python" -m uvicorn main:app --host 0.0.0.0 --port 8000
    ) &
    BACKEND_PID=$!
    echo "✅ Backend iniciado (PID: $BACKEND_PID)"
else
    echo "⚠️  Backend não iniciado - porta 8000 ocupada"
fi

# Iniciar frontend
if [ "$FRONTEND_OK" = true ]; then
    echo "🎨 Iniciando Frontend (porta 5173)..."
    (
        cd "$PROJECT_ROOT/client"
        npm run build
        npm run preview -- --host 0.0.0.0 --port 5173
    ) &
    FRONTEND_PID=$!
    echo "✅ Frontend iniciado (PID: $FRONTEND_PID)"
else
    echo "⚠️  Frontend não iniciado - porta 5173 ocupada"
fi

# Aguardar inicialização real
echo ""
echo "⏳ Aguardando serviços ficarem prontos..."
[ "$BACKEND_OK" = true ] && wait_for_http "Backend" "http://localhost:8000/health" 45
[ "$FRONTEND_OK" = true ] && wait_for_http "Frontend" "http://localhost:5173/" 90

# Verificar status
echo ""
echo "=== Status dos Serviços ==="
echo -n "Backend (porta 8000): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null; then
    echo "✅ OK"
else
    echo "❌ Fora do ar"
fi

echo -n "Frontend (porta 5173): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/ 2>/dev/null; then
    echo "✅ OK"
else
    echo "❌ Fora do ar"
fi

echo ""
echo "🌐 URLs de acesso:"
echo "  • Backend API: http://localhost:8000"
echo "  • Frontend (landing oficial): http://localhost:5173/welcome"
echo "  • Frontend (alias): http://localhost:5173"
echo "  • Frontend (compat legado): http://localhost:5173/landing-page.html"
echo ""
echo "Para parar todos os serviços: ./stop_platform.sh"
echo "Para verificar status: ./status_platform.sh"
