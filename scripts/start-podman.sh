#!/bin/bash
# ClimateWise - Startup com Podman Nativo
# Alternativa quando docker-compose não funciona

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ClimateWise - Startup com Podman${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Carregar .env
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ Carregando .env${NC}"
    set -a
    source .env
    set +a
else
    echo -e "${YELLOW}⚠ .env não encontrado, usando padrões${NC}"
    export DB_USER=postgres
    export DB_PASSWORD=climatewise123
    export DB_NAME=climatewise
    export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    export OTEL_ENABLED=true
fi

# Criar rede
echo -e "${BLUE}Criando rede...${NC}"
podman network create climatewise 2>/dev/null || echo "Rede já existe"
podman network create monitoring 2>/dev/null || echo "Rede já existe"

# Criar volumes
echo -e "${BLUE}Criando volumes...${NC}"
podman volume create postgres_data 2>/dev/null || echo "Volume postgres_data já existe"
podman volume create redis_data 2>/dev/null || echo "Volume redis_data já existe"
podman volume create prometheus_data 2>/dev/null || echo "Volume prometheus_data já existe"
podman volume create grafana_data 2>/dev/null || echo "Volume grafana_data já existe"

# Iniciar serviços base
echo -e "${BLUE}Iniciando serviços base...${NC}"

# PostgreSQL
echo -e "  ${GREEN}✓${NC} PostgreSQL"
podman run -d \
    --name climatewise-db \
    --network climatewise \
    -e POSTGRES_USER=${DB_USER:-postgres} \
    -e POSTGRES_PASSWORD=${DB_PASSWORD:-climatewise123} \
    -e POSTGRES_DB=${DB_NAME:-climatewise} \
    -p 5432:5432 \
    -v postgres_data:/var/lib/postgresql/data \
    --restart unless-stopped \
    postgres:16-alpine 2>/dev/null || podman restart climatewise-db

# Redis
echo -e "  ${GREEN}✓${NC} Redis"
podman run -d \
    --name climatewise-redis \
    --network climatewise \
    -p 6379:6379 \
    -v redis_data:/data \
    --restart unless-stopped \
    redis:7-alpine 2>/dev/null || podman restart climatewise-redis

# OTel Collector
echo -e "  ${GREEN}✓${NC} OTel Collector"
podman run -d \
    --name otel-collector \
    --network monitoring \
    -p 4317:4317 \
    -p 4318:4318 \
    -p 8888:8888 \
    -v ./monitoring/otel-collector-config.yaml:/etc/otelcol-contrib/config.yaml:ro \
    --restart unless-stopped \
    otel/opentelemetry-collector-contrib:0.110.0 2>/dev/null || podman restart otel-collector

# Jaeger
echo -e "  ${GREEN}✓${NC} Jaeger"
podman run -d \
    --name jaeger \
    --network monitoring \
    -p 16686:16686 \
    -p 14250:14250 \
    -e COLLECTOR_OTLP_ENABLED=true \
    --restart unless-stopped \
    jaegertracing/all-in-one:1.62.0 2>/dev/null || podman restart jaeger

# Prometheus
echo -e "  ${GREEN}✓${NC} Prometheus"
podman run -d \
    --name prometheus \
    --network monitoring \
    -p 9090:9090 \
    -v ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro \
    -v ./monitoring/prometheus-rules.yml:/etc/prometheus/rules.yml:ro \
    -v prometheus_data:/prometheus \
    --restart unless-stopped \
    prom/prometheus:v2.54.1 \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/prometheus \
    --storage.tsdb.retention.time=15d \
    --web.enable-lifecycle 2>/dev/null || podman restart prometheus

# Grafana
echo -e "  ${GREEN}✓${NC} Grafana"
podman run -d \
    --name grafana \
    --network monitoring \
    -p 3000:3000 \
    -e GF_SECURITY_ADMIN_USER=admin \
    -e GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin} \
    -v grafana_data:/var/lib/grafana \
    -v ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro \
    --restart unless-stopped \
    grafana/grafana:11.3.0 2>/dev/null || podman restart grafana

# Zipkin
echo -e "  ${GREEN}✓${NC} Zipkin"
podman run -d \
    --name zipkin \
    --network monitoring \
    -p 9411:9411 \
    --restart unless-stopped \
    openzipkin/zipkin:3.4.0 2>/dev/null || podman restart zipkin

# Tempo
echo -e "  ${GREEN}✓${NC} Tempo"
podman run -d \
    --name tempo \
    --network monitoring \
    -p 3200:3200 \
    --restart unless-stopped \
    grafana/tempo:2.6.1 \
    -config.file=/etc/tempo/config.yaml 2>/dev/null || podman restart tempo

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Serviços iniciados com sucesso!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📊 URLs dos Serviços:${NC}"
echo ""
echo -e "  ${GREEN}✓${NC} Grafana:      ${BLUE}http://localhost:3000${NC} (admin/admin)"
echo -e "  ${GREEN}✓${NC} Prometheus:   ${BLUE}http://localhost:9090${NC}"
echo -e "  ${GREEN}✓${NC} Jaeger:       ${BLUE}http://localhost:16686${NC}"
echo -e "  ${GREEN}✓${NC} Zipkin:       ${BLUE}http://localhost:9411${NC}"
echo -e "  ${GREEN}✓${NC} OTel Health:  ${BLUE}http://localhost:13133/health${NC} (se disponível)"
echo ""
echo -e "${BLUE}📋 Comandos Úteis:${NC}"
echo ""
echo "  # Ver status dos containers"
echo "  podman ps"
echo ""
echo "  # Ver logs"
echo "  podman logs -f otel-collector"
echo ""
echo "  # Parar todos"
echo "  podman stop climatewise-db climatewise-redis otel-collector jaeger prometheus grafana zipkin tempo"
echo ""
echo "  # Remover todos"
echo "  podman rm -f climatewise-db climatewise-redis otel-collector jaeger prometheus grafana zipkin tempo"
echo ""
