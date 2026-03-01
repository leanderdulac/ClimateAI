#!/bin/bash

# Script para iniciar toda a plataforma ClimateWise

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

# Verificar portas
echo "📊 Verificando portas..."
check_port 8000 && BACKEND_OK=true || BACKEND_OK=false
check_port 3000 && FRONTEND_OK=true || FRONTEND_OK=false
check_port 8080 && LANDING_OK=true || LANDING_OK=false

# Iniciar backend
if [ "$BACKEND_OK" = true ]; then
    echo "🔧 Iniciando Backend (porta 8000)..."
    (
        cd server
        source ../.venv/bin/activate
        PYTHONPATH=. ../.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ) &
    BACKEND_PID=$!
    echo "✅ Backend iniciado (PID: $BACKEND_PID)"
else
    echo "⚠️  Backend não iniciado - porta 8000 ocupada"
fi

# Aguardar backend inicializar
sleep 3

# Iniciar frontend
if [ "$FRONTEND_OK" = true ]; then
    echo "🎨 Iniciando Frontend (porta 3000)..."
    (
        cd client
        npm run dev -- --host 0.0.0.0 --port 3000
    ) &
    FRONTEND_PID=$!
    echo "✅ Frontend iniciado (PID: $FRONTEND_PID)"
else
    echo "⚠️  Frontend não iniciado - porta 3000 ocupada"
fi

# Iniciar landing page
if [ "$LANDING_OK" = true ]; then
    echo "📄 Iniciando Landing Page (porta 8080)..."
    python3 -m http.server 8080 --bind 0.0.0.0 &
    LANDING_PID=$!
    echo "✅ Landing Page iniciada (PID: $LANDING_PID)"
else
    echo "⚠️  Landing Page não iniciada - porta 8080 ocupada"
fi

# Aguardar inicialização
sleep 5

# Verificar status
echo ""
echo "=== Status dos Serviços ==="
echo -n "Backend (porta 8000): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ 2>/dev/null; then
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

echo -n "Landing Page (porta 8080): "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/landing-page.html 2>/dev/null; then
    echo "✅ OK"
else
    echo "❌ Fora do ar"
fi

echo ""
echo "🌐 URLs de acesso:"
echo "  • Backend API: http://localhost:8000"
echo "  • Frontend: http://localhost:3000"
echo "  • Landing Page: http://localhost:8080/landing-page.html"
echo ""
echo "Para parar todos os serviços: ./stop_platform.sh"
echo "Para verificar status: ./status_platform.sh"
