#!/bin/bash

# Script de teste da integração Landing Page ↔ Dashboard

echo "🧪 Testando Integração Landing Page ↔ Dashboard"
echo "=============================================="

# Verificar se os serviços estão rodando
echo ""
echo "📊 Verificando status dos serviços..."

# Backend
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Backend (porta 8000): OK"
else
    echo "❌ Backend (porta 8000): FALHA"
fi

# Frontend/Dashboard
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend/Dashboard (porta 3000): OK"
else
    echo "❌ Frontend/Dashboard (porta 3000): FALHA"
fi

# Landing Page
if curl -s http://localhost:8080/landing-page.html > /dev/null; then
    echo "✅ Landing Page (porta 8080): OK"
else
    echo "❌ Landing Page (porta 8080): FALHA"
fi

# Página de boas-vindas
if curl -s http://localhost:3000/welcome > /dev/null; then
    echo "✅ Página de Boas-Vindas (/welcome): OK"
else
    echo "❌ Página de Boas-Vindas (/welcome): FALHA"
fi

echo ""
echo "🔗 Testando links da landing page..."

# Verificar se os links estão corretos
LANDING_CONTENT=$(curl -s http://localhost:8080/landing-page.html)

if echo "$LANDING_CONTENT" | grep -q "http://localhost:3000/welcome"; then
    echo "✅ Links da landing page apontam para dashboard: OK"
else
    echo "❌ Links da landing page não estão corretos: FALHA"
fi

echo ""
echo "🎯 Teste concluído!"
echo ""
echo "Para testar a integração completa:"
echo "1. Abra http://localhost:8080/landing-page.html"
echo "2. Clique em 'Acessar Dashboard'"
echo "3. Deve redirecionar para http://localhost:3000/welcome"
echo "4. Na página de boas-vindas, clique em 'Explorar Dashboard'"
echo "5. Deve levar para o dashboard principal"
