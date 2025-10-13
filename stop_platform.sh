#!/bin/bash

# Script para parar toda a plataforma ClimateAI

echo "🛑 Parando Plataforma ClimateAI..."

# Parar processos
echo "🔧 Parando Backend..."
pkill -f "uvicorn.*main:app" || echo "Nenhum processo backend encontrado"

echo "🎨 Parando Frontend..."
pkill -f "vite\|npm.*dev" || echo "Nenhum processo frontend encontrado"

echo "📄 Parando Landing Page..."
pkill -f "python3 -m http.server" || echo "Nenhum processo landing page encontrado"

# Aguardar
sleep 2

# Verificar se pararam
echo ""
echo "=== Verificação Final ==="
if pgrep -f "uvicorn.*main:app" > /dev/null; then
    echo "❌ Backend ainda rodando"
else
    echo "✅ Backend parado"
fi

if pgrep -f "vite\|npm.*dev" > /dev/null; then
    echo "❌ Frontend ainda rodando"
else
    echo "✅ Frontend parado"
fi

if pgrep -f "python3 -m http.server" > /dev/null; then
    echo "❌ Landing Page ainda rodando"
else
    echo "✅ Landing Page parada"
fi

echo ""
echo "🧹 Plataforma parada com sucesso!"