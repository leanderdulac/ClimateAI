#!/bin/bash

# ============================================
# Verificação Completa de APIs - ClimateAI
# ============================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Verificação Completa de APIs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Contadores
APIS_OK=0
APIS_WARN=0
APIS_FAIL=0

# Função para testar API
test_api() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    local data=${4:-}
    
    echo -n "Testando $name... "
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -X POST "$url" -H "Content-Type: application/json" -d "$data" 2>/dev/null)
    else
        response=$(curl -s "$url" 2>/dev/null)
    fi
    
    if [ -z "$response" ]; then
        echo -e "${RED}✗ Falhou (sem resposta)${NC}"
        ((APIS_FAIL++))
        return 1
    fi
    
    # Verificar se é JSON válido
    if echo "$response" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        ((APIS_OK++))
        return 0
    else
        echo -e "${YELLOW}⚠ Resposta inválida${NC}"
        ((APIS_WARN++))
        return 1
    fi
}

# 1. Health Check
echo "━━━ 1. Health Check ━━━"
test_api "Backend Health" "http://localhost:8000/health"
echo ""

# 2. APIs de Clima
echo "━━━ 2. APIs de Clima ━━━"
test_api "Embrapa/OpenMeteo (Histórico)" \
    "http://localhost:8000/api/v1/clima/historico?latitude=-23.5505&longitude=-46.6333&data_inicio=2026-02-01&data_fim=2026-02-16"

test_api "OpenMeteo (Previsão)" \
    "http://localhost:8000/api/v1/xweather/brazil-forecast?latitude=-23.5505&longitude=-46.6333&days=7"

test_api "Clima Atual" \
    "http://localhost:8000/api/v1/clima/atual?latitude=-23.5505&longitude=-46.6333"
echo ""

# 3. APIs de Localização
echo "━━━ 3. APIs de Localização ━━━"
test_api "Busca de Cidades" \
    "http://localhost:8000/api/v1/localizacao/cidade/busca?termo=Sao%20Paulo&estado=SP"

test_api "CEP" \
    "http://localhost:8000/api/v1/localizacao/cep/01310100"
echo ""

# 4. APIs de Modelagem
echo "━━━ 4. APIs de Modelagem ━━━"
test_api "Policy Pricing" \
    "http://localhost:8000/api/v1/policy-pricing/calculate" \
    "POST" \
    '{"asset_value":100000,"severity_amount":10000,"frequency_pct":10,"coverage_period_years":1,"scr_score":450,"is_manual_underwriting":false}'

test_api "Pricing" \
    "http://localhost:8000/api/v1/pricing/calculate" \
    "POST" \
    '{"location_id":"SP","coverage_amount":100000}'
echo ""

# 5. APIs de IA
echo "━━━ 5. APIs de IA ━━━"
test_api "Health Check" \
    "http://localhost:8000/api/v1/health"
echo ""

# 6. Frontend
echo "━━━ 6. Frontend ━━━"
echo -n "Verificando frontend... "
if curl -s http://localhost:3000/ | grep -q "ClimateWise\|ClimateAI"; then
    echo -e "${GREEN}✓ Carregando${NC}"
    ((APIS_OK++))
else
    echo -e "${YELLOW}⚠ Pode não estar rodando${NC}"
    ((APIS_WARN++))
fi
echo ""

# 7. Configuração do Frontend
echo "━━━ 7. Configuração do Frontend ━━━"
if [ -f "client/.env" ]; then
    echo "Arquivo client/.env encontrado:"
    cat client/.env | grep -v "^#" | grep -v "^$"
else
    echo -e "${YELLOW}⚠ client/.env não encontrado${NC}"
    if [ -f "client/.env.example" ]; then
        echo "Copiando de client/.env.example..."
        cp client/.env.example client/.env
    fi
fi
echo ""

# Resumo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Resumo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ Funcionando:${NC} $APIS_OK"
echo -e "${YELLOW}⚠ Alertas:${NC}    $APIS_WARN"
echo -e "${RED}✗ Falhas:${NC}      $APIS_FAIL"
echo ""

if [ $APIS_FAIL -eq 0 ] && [ $APIS_WARN -eq 0 ]; then
    echo -e "${GREEN}✅ Todas as APIs estão funcionando!${NC}"
    exit 0
elif [ $APIS_FAIL -eq 0 ]; then
    echo -e "${YELLOW}⚠️  APIs funcionando com alertas${NC}"
    exit 0
else
    echo -e "${RED}❌ Algumas APIs estão com problemas${NC}"
    exit 1
fi
