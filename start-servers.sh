#!/bin/bash
# Script para iniciar Backend e Frontend do ClimateWise

echo "================================================"
echo "  ClimateWise - Iniciando Servidores"
echo "================================================"
echo ""

# Função para verificar se um processo está rodando
check_port() {
  lsof -i :$1 > /dev/null 2>&1
  return $?
}

# Matar processos existentes
echo "🧹 Limpando processos antigos..."
pkill -9 -f "uvicorn.*main:app" 2>/dev/null
pkill -9 -f "vite" 2>/dev/null
sleep 2

# Iniciar Backend
echo ""
echo "🚀 Iniciando Backend (Porta 8000)..."
cd /home/exp/Downloads/ClimateAI/server

if [ ! -d "venv-hathor" ]; then
  echo "❌ Virtual environment não encontrado!"
  echo "Execute: cd server && python3 -m venv venv-hathor && source venv-hathor/bin/activate && pip install -r requirements.txt"
  exit 1
fi

source venv-hathor/bin/activate

# Set environment variables for development
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export DATABASE_ENABLED=false
export SECRET_KEY="dev-secret-key-not-for-production-use-only"
export DEBUG=true
export ALLOW_ORIGINS="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

# Start backend in background
nohup python3 -m uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-dir blockchain \
  --reload-dir api \
  > /tmp/backend.log 2>&1 &

BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Aguardar backend iniciar
echo "   Aguardando backend iniciar..."
for i in {1..30}; do
  if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "   ✅ Backend pronto!"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "   ❌ Backend falhou ao iniciar. Logs:"
    tail -50 /tmp/backend.log
    exit 1
  fi
  sleep 1
done

# Iniciar Frontend
echo ""
echo "🎨 Iniciando Frontend (Porta 5173)..."
cd /home/exp/Downloads/ClimateAI/client

if [ ! -d "node_modules" ]; then
  echo "❌ node_modules não encontrado!"
  echo "Execute: cd client && npm install"
  exit 1
fi

# Start frontend in background
nohup npm run dev \
  -- --host 0.0.0.0 --port 5173 \
  > /tmp/frontend.log 2>&1 &

FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# Aguardar frontend iniciar
echo "   Aguardando frontend iniciar..."
for i in {1..20}; do
  if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "   ✅ Frontend pronto!"
    break
  fi
  if [ $i -eq 20 ]; then
    echo "   ⚠️  Frontend pode estar com problemas. Logs:"
    tail -30 /tmp/frontend.log
  fi
  sleep 1
done

# Resumo final
echo ""
echo "================================================"
echo "  ✅ Servidores Iniciados com Sucesso!"
echo "================================================"
echo ""
echo "📍 Acessos:"
echo "   • Frontend: http://localhost:5173"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Oracle Page: http://localhost:5173/oracle"
echo "   • Tokenização: http://localhost:5173/tokenization"
echo ""
echo "📊 Status:"
echo "   • Backend PID: $BACKEND_PID"
echo "   • Frontend PID: $FRONTEND_PID"
echo ""
echo "🛑 Para parar:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   ou: pkill -f 'uvicorn.*main' && pkill -f 'vite'"
echo ""
echo "📝 Logs:"
echo "   • Backend: /tmp/backend.log"
echo "   • Frontend: /tmp/frontend.log"
echo "================================================"

# Manter script rodando
wait
