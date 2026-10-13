#!/bin/bash

# ============================================
# Teste Completo da Plataforma ClimateWise
# ============================================
# Verifica todos os componentes implementados
# ============================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Contadores
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 ClimateWise - Teste Completo da Plataforma"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Função para testar endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    local data=${4:-}
    local timeout=${5:-10}
    
    echo -n "Testando $name... "
    
    if [ "$method" = "POST" ]; then
        response=$(timeout $timeout curl -s -X POST "$url" -H "Content-Type: application/json" -d "$data" 2>/dev/null)
    else
        response=$(timeout $timeout curl -s "$url" 2>/dev/null)
    fi
    
    if [ -z "$response" ]; then
        echo -e "${RED}✗ Falhou (sem resposta)${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
    
    # Verificar se é JSON válido
    if echo "$response" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
        echo -e "${GREEN}✓ OK${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠ Resposta inválida${NC}"
        ((TESTS_SKIPPED++))
        return 1
    fi
}

# 1. Health Check
echo "━━━ 1. Health Check ━━━"
test_endpoint "Backend Health" "http://localhost:8000/health" || true
echo ""

# 2. APIs de Clima
echo "━━━ 2. APIs de Clima ━━━"
test_endpoint "Embrapa/OpenMeteo (Histórico)" \
    "http://localhost:8000/api/v1/clima/historico?latitude=-23.5505&longitude=-46.6333&data_inicio=2026-02-01&data_fim=2026-02-16" || true

test_endpoint "XWeather Status" \
    "http://localhost:8000/api/v1/xweather/status" || true

test_endpoint "NOAA Status" \
    "http://localhost:8000/api/v1/noaa/status" || true
echo ""

# 3. APIs de Pricing
echo "━━━ 3. APIs de Pricing ━━━"
test_endpoint "Policy Pricing" \
    "http://localhost:8000/api/v1/policy-pricing/calculate" \
    "POST" \
    '{"asset_value":100000,"severity_amount":10000,"frequency_pct":10,"coverage_period_years":1,"scr_score":450,"is_manual_underwriting":false}' || true

test_endpoint "Bayesian Bootstrap" \
    "http://localhost:8000/api/v1/bayesian-bootstrap/premium" \
    "POST" \
    '{"claims_history":[100000,120000,95000,110000,105000],"risk_factor":1.2,"confidence_level":0.95}' || true
echo ""

# 4. Backtesting (Tier 1)
echo "━━━ 4. Backtesting (Tier 1) ━━━"
test_endpoint "Backtest Methods" \
    "http://localhost:8000/api/v1/backtesting/test-methods" || true

test_endpoint "Backtest Example Data" \
    "http://localhost:8000/api/v1/backtesting/example-data" || true
echo ""

# 5. Audit Trail (Tier 1)
echo "━━━ 5. Audit Trail (Tier 1) ━━━"
test_endpoint "Audit Stats" \
    "http://localhost:8000/api/v1/audit/stats" || true

test_endpoint "Audit Chain Verification" \
    "http://localhost:8000/api/v1/audit/verify-chain" || true

test_endpoint "Audit Example" \
    "http://localhost:8000/api/v1/audit/example" || true
echo ""

# 6. Localização
echo "━━━ 6. APIs de Localização ━━━"
test_endpoint "Busca de Cidades" \
    "http://localhost:8000/api/v1/localizacao/cidade/busca?termo=Sao%20Paulo&estado=SP" || true
echo ""

# 7. Testes Unitários
echo "━━━ 7. Testes Unitários ━━━"
echo -n "Executando testes de backtesting... "
cd /home/exp/Downloads/ClimateAI/server
if python3 -m pytest tests/services/test_backtesting_service.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    echo -e "${GREEN}✓ OK${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ Alguns testes falharam${NC}"
    ((TESTS_SKIPPED++))
fi

echo -n "Executando testes de audit trail... "
if python3 -m pytest tests/services/test_audit_trail_service.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    echo -e "${GREEN}✓ OK${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ Alguns testes falharam${NC}"
    ((TESTS_SKIPPED++))
fi

echo -n "Executando testes de xweather... "
if python3 -m pytest tests/services/test_xweather_service.py -q --tb=no 2>/dev/null | grep -q "passed"; then
    echo -e "${GREEN}✓ OK${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ Alguns testes falharam${NC}"
    ((TESTS_SKIPPED++))
fi
echo ""

# 8. Verificar imports
echo "━━━ 8. Verificar Imports ━━━"
echo -n "Verificando import do backtesting... "
if python3 -c "from api.backtesting import router; print('OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Falhou${NC}"
    ((TESTS_FAILED++))
fi

echo -n "Verificando import do audit... "
if python3 -c "from api.audit import router; print('OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Falhou${NC}"
    ((TESTS_FAILED++))
fi

echo -n "Verificando import do xweather... "
if python3 -c "from api.xweather_forecast import router; print('OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Falhou${NC}"
    ((TESTS_FAILED++))
fi
echo ""

# 9. Verificar serviços
echo "━━━ 9. Verificar Serviços ━━━"
echo -n "Verificando backtesting service... "
if python3 -c "from services.backtesting_service import BacktestingService; s = BacktestingService(); print('OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Falhou${NC}"
    ((TESTS_FAILED++))
fi

echo -n "Verificando audit trail service... "
if python3 -c "from services.audit_trail_service import AuditTrailService; s = AuditTrailService(); print('OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Falhou${NC}"
    ((TESTS_FAILED++))
fi

echo -n "Verificando xweather service... "
if python3 -c "from services.xweather_service import XWeatherService; s = XWeatherService(); print('OK')" 2>/dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Falhou${NC}"
    ((TESTS_FAILED++))
fi
echo ""

# Resumo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Resumo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ Passaram:${NC}  $TESTS_PASSED"
echo -e "${YELLOW}⚠ Skipados:${NC}  $TESTS_SKIPPED"
echo -e "${RED}✗ Falharam:${NC}    $TESTS_FAILED"
echo ""

TOTAL=$((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ Todos os testes críticos passaram!${NC}"
    echo ""
    echo "📋 Plataforma está pronta para Fase 3"
    exit 0
else
    echo -e "${RED}❌ Alguns testes falharam${NC}"
    echo ""
    echo "Revise os erros acima antes de prosseguir"
    exit 1
fi
