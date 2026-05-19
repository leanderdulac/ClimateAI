#!/bin/bash
# ClimateWise - Startup do Stack de Monitoramento Tier 1
# Este script inicia todo o stack de observabilidade (OTel, Prometheus, Grafana, Jaeger)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

generate_secret() {
    python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(24))
PY
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ClimateWise - Monitoring Stack Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar se docker-compose está disponível
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Erro: docker-compose não encontrado!${NC}"
    exit 1
fi

# Determinar qual comando usar (docker-compose ou docker compose)
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Função para verificar se um serviço está rodando
check_service() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo -ne "${YELLOW}Verificando $service...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s --connect-timeout 1 http://localhost:$port > /dev/null 2>&1; then
            echo -e "${GREEN} OK${NC}"
            return 0
        fi
        echo -ne "."
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED} Falhou${NC}"
    return 1
}

# Carregar variáveis de ambiente
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ Carregando variáveis de ambiente do .env${NC}"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}⚠ Aviso: Arquivo .env não encontrado. Gerando credenciais efêmeras.${NC}"
    export OTEL_ENABLED=true
    export GRAFANA_ADMIN_PASSWORD="$(generate_secret)"
fi

# Criar diretórios necessários
echo -e "${BLUE}✓ Criando diretórios de dados...${NC}"
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/provisioning
mkdir -p prometheus
mkdir -p otel-logs

# Iniciar stack de monitoramento
echo ""
echo -e "${BLUE}Iniciando stack de monitoramento...${NC}"
echo ""

# Iniciar serviços
$COMPOSE_CMD -f docker-compose.yml -f docker-compose.otel.yml up -d \
    otel-collector \
    jaeger \
    prometheus \
    grafana \
    tempo \
    zipkin

echo ""
echo -e "${BLUE}Aguardando serviços inicializarem...${NC}"
sleep 10

# Verificar saúde dos serviços
echo ""
echo -e "${BLUE}Verificando saúde dos serviços...${NC}"

check_service "Prometheus" "9090" || true
check_service "Grafana" "3000" || true
check_service "Jaeger" "16686" || true
check_service "OTel Collector Health" "13133" || true

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Monitoramento iniciado com sucesso!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📊 Dashboards e Serviços:${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} Grafana:      ${BLUE}http://localhost:3000${NC} (admin/${GRAFANA_ADMIN_PASSWORD})"
echo -e "  ${GREEN}✓${NC} Prometheus:   ${BLUE}http://localhost:9090${NC}"
echo -e "  ${GREEN}✓${NC} Jaeger:       ${BLUE}http://localhost:16686${NC}"
echo -e "  ${GREEN}✓${NC} Zipkin:       ${BLUE}http://localhost:9411${NC}"
echo -e "  ${GREEN}✓${NC} OTel Health:  ${BLUE}http://localhost:13133/health${NC}"
echo ""
echo -e "${BLUE}📚 Próximos passos:${NC}"
echo ""
echo "  1. Configure o datasource do Prometheus no Grafana"
echo "     URL: http://prometheus:9090"
echo ""
echo "  2. Importe o dashboard de SLO:"
echo "     monitoring/grafana/dashboards/slo-overview.json"
echo ""
echo "  3. Verifique os traces no Jaeger:"
echo "     Service: climatewise-backend"
echo ""
echo "  4. Para ver logs do OTel Collector:"
echo "     $COMPOSE_CMD -f docker-compose.yml -f docker-compose.otel.yml logs -f otel-collector"
echo ""
echo -e "${YELLOW}⚠ Para parar o stack:${NC}"
echo "  $COMPOSE_CMD -f docker-compose.yml -f docker-compose.otel.yml down"
echo ""
echo -e "${YELLOW}⚠ Para parar e remover volumes (dados):${NC}"
echo "  $COMPOSE_CMD -f docker-compose.yml -f docker-compose.otel.yml down -v"
echo ""
