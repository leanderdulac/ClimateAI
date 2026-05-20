#!/bin/bash

# Script para verificar status da plataforma ClimateWise

echo "📊 Status da Plataforma ClimateWise"
echo "================================="

# Verificar processos
echo ""
echo "🔍 Processos em execução:"
echo -n "Backend (uvicorn): "
if pgrep -f "uvicorn.*main:app" > /dev/null; then
    echo "✅ Rodando"
else
    echo "❌ Parado"
fi

echo -n "Frontend (vite): "
if pgrep -f "vite preview" > /dev/null || pgrep -f "npm run preview" > /dev/null || pgrep -f "npm.*dev" > /dev/null || pgrep -f "node .*node_modules/.bin/vite preview" > /dev/null; then
    echo "✅ Rodando"
else
    echo "❌ Parado"
fi

# Verificar conectividade
echo ""
echo "🌐 Conectividade dos serviços:"
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

# Informações adicionais
echo ""
echo "📋 Informações adicionais:"
echo "Data/Hora: $(date)"
echo "Usuário: $(whoami)"
echo "Diretório: $(pwd)"

echo ""
echo "💡 Comandos disponíveis:"
echo "  • Iniciar plataforma: ./start_platform.sh"
echo "  • Parar plataforma: ./stop_platform.sh"
echo "  • Verificar status: ./status_platform.sh"
