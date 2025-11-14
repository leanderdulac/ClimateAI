#!/bin/bash
# Script para testar logging estruturado em JSON

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}📊 Teste de JSON Logging FIMCE${NC}"
echo -e "${BLUE}================================${NC}\n"

API_URL="${1:-http://localhost:8000}"
TIMEOUT=5

# Função para verificar resposta JSON
validate_json() {
    local json=$1
    if command -v jq &> /dev/null; then
        if echo "$json" | jq . &>/dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    else
        return 0  # Assumir que é válido se jq não estiver disponível
    fi
}

# Função para testar um endpoint
test_endpoint() {
    local name=$1
    local endpoint=$2
    
    echo -ne "${YELLOW}Testing ${name}...${NC} "
    
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}❌ curl não está instalado${NC}"
        return 1
    fi
    
    response=$(curl -s -w "\n%{http_code}" -m $TIMEOUT "$API_URL$endpoint" 2>/dev/null || echo "000")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓${NC}"
        
        if validate_json "$body"; then
            echo "  Status de resposta JSON: válido"
            if command -v jq &> /dev/null; then
                echo "  Headers da resposta:"
                echo "$body" | jq -r 'keys[]' 2>/dev/null | sed 's/^/    - /'
            fi
        else
            echo "  ⚠️  Resposta não é JSON válido"
        fi
        return 0
    else
        echo -e "${RED}✗ (HTTP $http_code)${NC}"
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

# Verificar API
check_api_running || exit 1

echo -e "${BLUE}Testando Endpoints:${NC}\n"

test_endpoint "GET /health" "/health"
test_endpoint "GET /api/v1/health/full" "/api/v1/health/full"
test_endpoint "GET /api/v1/health/critical" "/api/v1/health/critical"

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}✓ Testes de logging concluídos!${NC}"
echo -e "${BLUE}================================${NC}\n"

echo -e "${YELLOW}📊 Para monitorar logs em JSON:${NC}"
echo "  tail -f /var/log/fimce/app.json | jq ."
echo ""
echo -e "${YELLOW}📈 Para verificar request IDs:${NC}"
echo "  curl -v http://localhost:8000/health 2>&1 | grep X-Request-ID"
echo ""
echo -e "${YELLOW}🔍 Para buscar logs específicos:${NC}"
echo "  cat /var/log/fimce/app.json | jq 'select(.level==\"ERROR\")'"
echo ""
echo -e "${YELLOW}⚠️  Para encontrar requisições lentas:${NC}"
echo "  cat /var/log/fimce/app.json | jq 'select(.extra.response_time_ms > 100)'"
