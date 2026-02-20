#!/bin/bash

# ============================================
# Teste do Cálculo de Prêmio - ClimateAI
# ============================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Teste - Cálculo de Prêmio (Pricing)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Teste 1: Health Check
echo "1️⃣  Testando Health Check..."
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q "healthy\|status"; then
    echo -e "${GREEN}✓ Backend está rodando${NC}"
else
    echo -e "${RED}✗ Backend não está respondendo${NC}"
    echo "Inicie com: cd server && python -m uvicorn main:app --reload"
    exit 1
fi

# Teste 2: Endpoint de Pricing
echo ""
echo "2️⃣  Testando Endpoint de Pricing..."
echo "Enviando requisição..."

RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/policy-pricing/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "asset_value": 100000,
    "severity_amount": 10000,
    "frequency_pct": 10,
    "coverage_period_years": 1,
    "scr_score": 450,
    "is_manual_underwriting": false,
    "latitude": -23.55,
    "longitude": -46.63
  }')

# Verifica se recebeu resposta
if [ -z "$RESPONSE" ]; then
    echo -e "${RED}✗ Nenhuma resposta do endpoint${NC}"
    exit 1
fi

# Verifica se tem erro
if echo "$RESPONSE" | grep -q "detail"; then
    echo -e "${RED}✗ Erro na API:${NC}"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    exit 1
fi

# Verifica se tem premium
if echo "$RESPONSE" | grep -q "total_premium"; then
    echo -e "${GREEN}✓ Endpoint de pricing está funcionando!${NC}"
    
    # Extrai e mostra o premium
    PREMIUM=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['financials']['total_premium'])" 2>/dev/null)
    STATUS=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
    NET_PROFIT=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['financials']['net_profit'])" 2>/dev/null)
    
    echo ""
    echo "📊 Resultado do Cálculo:"
    echo "   Status: $STATUS"
    echo "   Prêmio Total: R$ $PREMIUM"
    echo "   Lucro Líquido: R$ $NET_PROFIT"
    echo ""
    
    # Mostra detalhes
    echo "📋 Resposta completa:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null | head -30 || echo "$RESPONSE"
else
    echo -e "${RED}✗ Resposta inesperada${NC}"
    echo "$RESPONSE"
    exit 1
fi

# Teste 3: Verifica frontend
echo ""
echo "3️⃣  Verificando configuração do frontend..."

if [ -f "client/.env" ]; then
    if grep -q "VITE_API_BASE_URL=http://localhost:8000" client/.env; then
        echo -e "${GREEN}✓ Frontend configurado corretamente${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend pode estar com configuração incorreta${NC}"
        echo "Verifique client/.env"
    fi
else
    echo -e "${YELLOW}⚠ client/.env não encontrado${NC}"
    echo "Copie de client/.env.example"
fi

# Resumo
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Teste Concluído!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Se o backend está funcionando mas o frontend não:"
echo "  1. Abra o console do navegador (F12)"
echo "  2. Verifique os logs com prefixo [PricingSimulator]"
echo "  3. Confira se VITE_API_BASE_URL está correto"
echo "  4. Rebuild do frontend: cd client && npm run build"
echo ""
echo "Para mais detalhes, veja: TROUBLESHOOTING_PREMIO.md"
echo ""
