#!/bin/bash
# ClimateWise - Validação do Ambiente Tier 1
# Verifica se todos os componentes estão prontos para execução

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ClimateWise - Validação Tier 1${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Contador de validações
PASS=0
FAIL=0
WARN=0

# Função para validar
validate() {
    local name=$1
    local cmd=$2
    
    echo -ne "Validando $name... "
    
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗ Falhou${NC}"
        ((FAIL++))
        return 1
    fi
}

# Função para validar com aviso
validate_warn() {
    local name=$1
    local cmd=$2
    
    echo -ne "Validando $name... "
    
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
        ((PASS++))
        return 0
    else
        echo -e "${YELLOW}⚠ Aviso${NC}"
        ((WARN++))
        return 1
    fi
}

echo -e "${BLUE}=== Verificando Pré-requisitos ===${NC}"
echo ""

# Docker/Podman
validate_warn "Docker/Podman" "docker --version"

# Node.js
validate_warn "Node.js" "node --version"

# Python
validate_warn "Python" "python3 --version"

echo ""
echo -e "${BLUE}=== Verificando Arquivos de Configuração ===${NC}"
echo ""

# Arquivos essenciais
validate "docker-compose.yml" "test -f docker-compose.yml"
validate "docker-compose.otel.yml" "test -f docker-compose.otel.yml"
validate ".env.example" "test -f .env.example"

echo ""
echo -e "${BLUE}=== Verificando Implementações ===${NC}"
echo ""

# Backend
validate "Circuit Breaker" "test -f server/lib/resilient_http_client.py"
validate "Redis Cache" "test -f server/lib/redis_cache.py"
validate "Rate Limiter" "test -f server/middleware/advanced_rate_limiter.py"
validate "Redaction PII" "test -f server/middleware/redaction.py"
validate "OTel Service" "test -f server/services/otel.py"

# Frontend
validate "Request ID" "test -f client/src/lib/requestId.ts"
validate "Consent Hook" "test -f client/src/hooks/useConsent.ts"
validate "API Client" "test -f client/src/lib/api.ts"

# Monitoring
validate "OTel Config" "test -f monitoring/otel-collector-config.yaml"
validate "Prometheus Rules" "test -f monitoring/prometheus-rules.yml"
validate "Grafana Dashboard" "test -f monitoring/grafana/dashboards/slo-overview.json"

# CI/CD
validate "Security Workflow" "test -f .github/workflows/security-scan.yml"

# Documentação
validate "TIER1 Roadmap" "test -f TIER1_ROADMAP.md"
validate "TIER1 Implementações" "test -f TIER1_IMPLEMENTACOES.md"
validate "Guia de Integração" "test -f INTEGRACAO_RAPIDA.md"

echo ""
echo -e "${BLUE}=== Verificando Dependências ===${NC}"
echo ""

# Python dependencies
if [ -f server/requirements.txt ]; then
    validate_warn "tenacity" "grep -q 'tenacity' server/requirements.txt"
    validate_warn "opentelemetry" "grep -q 'opentelemetry' server/requirements.txt"
    validate_warn "redis" "grep -q 'redis' server/requirements.txt"
fi

# Node dependencies
if [ -f client/package.json ]; then
    validate_warn "openapi-typescript" "grep -q 'openapi-typescript' client/package.json"
fi

echo ""
echo -e "${BLUE}=== Resumo ===${NC}"
echo ""
echo -e "  ${GREEN}✓ Aprovados:${NC} $PASS"
echo -e "  ${RED}✗ Falharam:${NC} $FAIL"
echo -e "  ${YELLOW}⚠ Avisos:${NC} $WARN"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ Todos os arquivos estão presentes!${NC}"
    echo ""
    
    if [ $WARN -gt 0 ]; then
        echo -e "${YELLOW}⚠ Alguns pré-requisitos podem não estar instalados.${NC}"
        echo ""
    fi
    
    echo -e "${BLUE}Próximos passos:${NC}"
    echo ""
    echo "1. Crie o arquivo .env:"
    echo -e "   ${YELLOW}cp .env.example .env${NC}"
    echo ""
    echo "2. Edite o .env com suas credenciais:"
    echo -e "   ${YELLOW}nano .env${NC}"
    echo ""
    echo "3. Inicie o stack de monitoramento:"
    echo -e "   ${YELLOW}./scripts/start-monitoring.sh${NC}"
    echo ""
    echo "4. Ou inicie manualmente:"
    echo -e "   ${YELLOW}docker-compose -f docker-compose.yml -f docker-compose.otel.yml up -d${NC}"
    echo ""
    echo -e "${BLUE}URLs dos serviços (após iniciar):${NC}"
    echo "  - Grafana:      http://localhost:3000 (admin/admin)"
    echo "  - Prometheus:   http://localhost:9090"
    echo "  - Jaeger:       http://localhost:16686"
    echo "  - Zipkin:       http://localhost:9411"
    echo "  - Backend API:  http://localhost:8000"
    echo "  - Frontend:     http://localhost:5173"
    echo ""
else
    echo -e "${RED}✗ Alguns arquivos estão faltando!${NC}"
    echo ""
    echo "Por favor, verifique os arquivos listados acima."
    echo ""
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Validação concluída!${NC}"
echo -e "${BLUE}========================================${NC}"
