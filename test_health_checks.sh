#!/bin/bash
# Script para testar os endpoints de health check da API FIMCE

set -e

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🏥 Teste de Health Checks FIMCE${NC}"
echo -e "${BLUE}================================${NC}\n"

API_URL="${1:-http://localhost:8000}"
TIMEOUT=5

# Função para testar um endpoint
test_endpoint() {
    local name=$1
    local endpoint=$2
    local expected_status=$3

    echo -ne "${YELLOW}Testing ${name}...${NC} "

    if ! command -v curl &> /dev/null; then
        echo -e "${RED}❌ curl não está instalado${NC}"
        return 1
    fi

    response=$(curl -s -w "\n%{http_code}" -m $TIMEOUT "$API_URL$endpoint" 2>/dev/null || echo "000")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓${NC}"

        # Tentar fazer parse JSON
        if command -v jq &> /dev/null && [ ! -z "$body" ]; then
            echo "  Status: $(echo "$body" | jq -r '.status' 2>/dev/null || echo 'N/A')"
            if echo "$body" | jq -e '.checks' &>/dev/null 2>&1; then
                echo "  Checks found: $(echo "$body" | jq '.checks | keys[]' 2>/dev/null | wc -l)"
            fi
        fi

        return 0
    else
        echo -e "${RED}✗ (HTTP $http_code, esperado $expected_status)${NC}"
        [ ! -z "$body" ] && echo "  Resposta: $body"
        return 1
    fi
}

# Função para verificar se a API está rodando
check_api_running() {
    echo -e "${YELLOW}Verificando se a API está rodando em $API_URL...${NC}"

    if curl -s -m 2 "$API_URL/health" &>/dev/null; then
        echo -e "${GREEN}✓ API está rodando${NC}\n"
        return 0
    else
        echo -e "${RED}✗ API não está rodando em $API_URL${NC}"
        echo -e "${YELLOW}Inicie o servidor com: cd server && uvicorn main:app --reload${NC}\n"
        return 1
    fi
}

# Executar testes
check_api_running || exit 1

echo -e "${BLUE}Testando Endpoints:${NC}\n"

test_endpoint "GET /health (compatibilidade)" "/health" "200"
test_endpoint "GET /api/v1/health/full (completo)" "/api/v1/health/full" "200"
test_endpoint "GET /api/v1/health/critical (crítico)" "/api/v1/health/critical" "200"

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}✓ Testes concluídos!${NC}"
echo -e "${BLUE}================================${NC}\n"

echo -e "${YELLOW}📊 Para monitoramento contínuo:${NC}"
echo "  watch -n 5 'curl -s http://localhost:8000/api/v1/health/full | jq'"
echo ""
echo -e "${YELLOW}📈 Para ver todas as métricas:${NC}"
echo "  curl http://localhost:8000/api/v1/health/full | jq '.'"
echo ""
echo -e "${YELLOW}⚡ Para check rápido (CI/CD):${NC}"
echo "  curl http://localhost:8000/api/v1/health/critical"
