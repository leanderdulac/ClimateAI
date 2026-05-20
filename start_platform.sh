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

# Verificar portas
echo "📊 Verificando portas..."
check_port 8000 && BACKEND_OK=true || BACKEND_OK=false
check_port 3000 && FRONTEND_OK=true || FRONTEND_OK=false

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
    echo "🎨 Iniciando Frontend (porta 3000)..."
    (
        cd "$PROJECT_ROOT/client"
        npm run build
        npm run preview -- --host 0.0.0.0 --port 3000
    ) &
    FRONTEND_PID=$!
    echo "✅ Frontend iniciado (PID: $FRONTEND_PID)"
else
    echo "⚠️  Frontend não iniciado - porta 3000 ocupada"
fi

# Aguardar inicialização real
echo ""
echo "⏳ Aguardando serviços ficarem prontos..."
[ "$BACKEND_OK" = true ] && wait_for_http "Backend" "http://localhost:8000/health" 45
[ "$FRONTEND_OK" = true ] && wait_for_http "Frontend" "http://localhost:3000/" 90

# Verificar status
echo ""
echo "=== Status dos Serviços ==="
echo -n "Backend (porta 8000): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null; then
    echo "✅ OK"
else
    echo "❌ Fora do ar"
fi

echo -n "Frontend (porta 3000): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ 2>/dev/null; then
    echo "✅ OK"
else
    echo "❌ Fora do ar"
fi

echo ""
echo "🌐 URLs de acesso:"
echo "  • Backend API: http://localhost:8000"
echo "  • Frontend (landing oficial): http://localhost:3000/welcome"
echo "  • Frontend (alias): http://localhost:3000"
echo "  • Frontend (compat legado): http://localhost:3000/landing-page.html"
echo ""
echo "Para parar todos os serviços: ./stop_platform.sh"
echo "Para verificar status: ./status_platform.sh"
