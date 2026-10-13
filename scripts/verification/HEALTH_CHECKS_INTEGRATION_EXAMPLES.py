"""
Exemplos de Integração - Health Checks FIMCE

Este arquivo contém exemplos práticos de como integrar os health checks
em diferentes contextos (Kubernetes, Docker, Nginx, CI/CD, etc)
"""

# ============================================================================
# 1. KUBERNETES DEPLOYMENT
# ============================================================================
kubernetes_deployment = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: climatewise-api
  labels:
    app: climatewise
spec:
  replicas: 3
  selector:
    matchLabels:
      app: climatewise
  template:
    metadata:
      labels:
        app: climatewise
    spec:
      containers:
      - name: api
        image: climatewise-api:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: climatewise-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: climatewise-secrets
              key: redis-url

        # Liveness probe - detecta se o container está vivo
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        # Readiness probe - detecta se está pronto para receber tráfego
        readinessProbe:
          httpGet:
            path: /api/v1/health/critical
            port: http
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2

        # Startup probe - aguarda inicialização completa
        startupProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 0
          periodSeconds: 2
          failureThreshold: 30  # 60 segundos total

---
apiVersion: v1
kind: Service
metadata:
  name: climatewise-api
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  selector:
    app: climatewise
"""

# ============================================================================
# 2. DOCKER COMPOSE
# ============================================================================
docker_compose = """
version: '3.9'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:password@db:5432/climatewise
      REDIS_URL: redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: climatewise
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
"""

# ============================================================================
# 3. DOCKERFILE COM HEALTHCHECK
# ============================================================================
dockerfile_content = """
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Health check integrado
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

# ============================================================================
# 4. NGINX LOAD BALANCER COM HEALTH CHECK
# ============================================================================
nginx_config = """
upstream climatewise_backend {
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;

    # Active health checking (requer módulo nginx_http_upstream_module)
    check interval=3000 rise=2 fall=5 timeout=1000 type=http;
    check_http_send "GET /health HTTP/1.0\\r\\n\\r\\n";
    check_http_expect_alive http_2xx;
}

server {
    listen 80;
    server_name api.climatewise.local;

    location / {
        proxy_pass http://climatewise_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 5s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Endpoint de status dos upstreams
    location /upstream_health {
        access_log off;
        default_type text/plain;
        return 200 "Upstream Health Status\\n";
    }
}
"""

# ============================================================================
# 5. CI/CD PIPELINE (GitHub Actions)
# ============================================================================
github_actions_workflow = """
name: Deploy e Health Check

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: password
          POSTGRES_DB: climatewise
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r server/requirements.txt

    - name: Start API server
      env:
        DATABASE_URL: postgresql://postgres:password@localhost:5432/climatewise
        REDIS_URL: redis://localhost:6379
      run: |
        cd server
        uvicorn main:app &
        sleep 5

    - name: Health Check Simple
      run: |
        curl -f http://localhost:8000/health || exit 1

    - name: Health Check Full
      run: |
        curl -f http://localhost:8000/api/v1/health/full || exit 1

    - name: Health Check Critical
      run: |
        curl -f http://localhost:8000/api/v1/health/critical || exit 1

    - name: Parse Health Status
      run: |
        STATUS=$(curl -s http://localhost:8000/api/v1/health/full | jq -r '.status')
        if [ "$STATUS" != "healthy" ]; then
          echo "❌ API Health Check Failed: $STATUS"
          exit 1
        fi
        echo "✓ API Health Status: $STATUS"

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'

    steps:
    - uses: actions/checkout@v3

    - name: Deploy to Kubernetes
      run: |
        kubectl apply -f k8s/deployment.yaml
        kubectl rollout status deployment/climatewise-api -n production

    - name: Verify Deployment Health
      run: |
        kubectl get pods -n production -l app=climatewise
        kubectl logs -n production -l app=climatewise --tail=10
"""

# ============================================================================
# 6. SCRIPT DE MONITORAMENTO CONTÍNUO
# ============================================================================
monitoring_script = """
#!/usr/bin/env python3
\"\"\"
Script de monitoramento contínuo dos health checks
\"\"\"

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, Any
import sys

class HealthMonitor:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.history = []
        self.threshold_alerts = {
            'cpu': 80,
            'memory': 80,
            'disk': 90,
        }

    async def check_health(self) -> Dict[str, Any]:
        \"\"\"Fazer health check da API\"\"\"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.api_url}/api/v1/health/full",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    return await resp.json()
            except Exception as e:
                return {"error": str(e), "status": "unhealthy"}

    def check_thresholds(self, data: Dict[str, Any]) -> list:
        \"\"\"Verificar se há violações de thresholds\"\"\"
        alerts = []

        if 'checks' in data and 'system' in data['checks']:
            system = data['checks']['system']

            if system.get('cpu_percent', 0) > self.threshold_alerts['cpu']:
                alerts.append(
                    f"⚠️  CPU alto: {system['cpu_percent']}%"
                )

            if system.get('memory_percent', 0) > self.threshold_alerts['memory']:
                alerts.append(
                    f"⚠️  Memória alta: {system['memory_percent']}%"
                )

            if system.get('disk_percent', 0) > self.threshold_alerts['disk']:
                alerts.append(
                    f"⚠️  Disco alto: {system['disk_percent']}%"
                )

        return alerts

    async def run(self, interval: int = 30):
        \"\"\"Rodar monitor continuamente\"\"\"
        print(f"🔍 Iniciando monitoramento de health checks")
        print(f"📍 API URL: {self.api_url}")
        print(f"⏱️  Intervalo: {interval}s\\n")

        try:
            while True:
                data = await self.check_health()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Exibir status
                status = data.get('status', 'unknown').upper()
                status_emoji = "✅" if status == "HEALTHY" else "⚠️" if status == "DEGRADED" else "❌"
                print(f"{status_emoji} [{timestamp}] Status: {status}")

                # Exibir checks
                if 'checks' in data:
                    for check_name, check_data in data['checks'].items():
                        check_status = check_data.get('status', 'unknown').upper()
                        check_emoji = "✓" if check_status == "HEALTHY" else "⚠" if check_status == "DEGRADED" else "✗"
                        response_time = check_data.get('response_time_ms', 0)
                        print(f"  {check_emoji} {check_name:15} {check_status:10} ({response_time:.1f}ms)")

                # Verificar alertas
                alerts = self.check_thresholds(data)
                for alert in alerts:
                    print(f"  {alert}")

                print()  # Linha em branco

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            print("\\n👋 Monitoramento encerrado")
            sys.exit(0)

async def main():
    monitor = HealthMonitor()
    await monitor.run(interval=10)

if __name__ == "__main__":
    asyncio.run(main())
"""

# ============================================================================
# 7. ALERTAS E NOTIFICAÇÕES
# ============================================================================
alerting_example = """
#!/usr/bin/env python3
\"\"\"
Exemplo de integração com sistemas de alerta (Slack, PagerDuty, etc)
\"\"\"

import aiohttp
import json
from enum import Enum

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

async def send_slack_alert(webhook_url: str, status: str, health_data: dict):
    \"\"\"Enviar alerta para Slack\"\"\"

    color = {
        "healthy": "#36a64f",
        "degraded": "#ff9800",
        "unhealthy": "#f44336",
    }.get(status, "#9e9e9e")

    payload = {
        "attachments": [
            {
                "color": color,
                "title": f"ClimateWise API Health - {status.upper()}",
                "fields": [
                    {
                        "title": "Database",
                        "value": health_data['checks']['database']['status'],
                        "short": True
                    },
                    {
                        "title": "Redis",
                        "value": health_data['checks']['redis']['status'],
                        "short": True
                    },
                    {
                        "title": "System CPU",
                        "value": f"{health_data['checks']['system']['cpu_percent']}%",
                        "short": True
                    },
                    {
                        "title": "Memory",
                        "value": f"{health_data['checks']['system']['memory_percent']}%",
                        "short": True
                    },
                ],
                "timestamp": health_data.get('timestamp')
            }
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=payload) as resp:
            return resp.status == 200

async def send_pagerduty_alert(integration_key: str, health_data: dict):
    \"\"\"Enviar alerta para PagerDuty\"\"\"

    status = health_data.get('status', 'unknown')
    severity = "critical" if status == "unhealthy" else "warning" if status == "degraded" else "info"

    payload = {
        "routing_key": integration_key,
        "event_action": "trigger",
        "dedup_key": f"climatewise-health-{int(health_data.get('timestamp', 0))}",
        "payload": {
            "summary": f"ClimateWise API Health: {status}",
            "severity": severity,
            "source": "ClimateWise API",
            "custom_details": health_data
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://events.pagerduty.com/v2/enqueue",
            json=payload
        ) as resp:
            return resp.status == 202

# Uso:
# await send_slack_alert(
#     webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
#     status="degraded",
#     health_data={...}
# )
"""

# ============================================================================
# 8. TESTES AUTOMATIZADOS
# ============================================================================
test_example = """
import pytest
import aiohttp
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_endpoint_simple():
    \"\"\"Teste do endpoint /health\"\"\"
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/health") as resp:
            assert resp.status == 200
            data = await resp.json()
            assert "status" in data
            assert data["status"] in ["healthy", "degraded", "unhealthy"]

@pytest.mark.asyncio
async def test_health_endpoint_full():
    \"\"\"Teste do endpoint /api/v1/health/full\"\"\"
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/api/v1/health/full") as resp:
            assert resp.status == 200
            data = await resp.json()

            # Validar estrutura
            assert "status" in data
            assert "timestamp" in data
            assert "checks" in data

            # Validar checks
            checks = data["checks"]
            assert "database" in checks
            assert "system" in checks

            # Validar que cada check tem as propriedades esperadas
            for check_name, check_data in checks.items():
                assert "status" in check_data
                assert "response_time_ms" in check_data

@pytest.mark.asyncio
async def test_health_database_connectivity():
    \"\"\"Teste de conectividade ao banco de dados\"\"\"
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/api/v1/health/critical") as resp:
            data = await resp.json()
            assert data["database"]["status"] == "healthy"

@pytest.mark.asyncio
async def test_health_response_time():
    \"\"\"Teste de tempo de resposta dos checks\"\"\"
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/api/v1/health/critical") as resp:
            data = await resp.json()

            # Health check crítico deve ser rápido (<100ms)
            total_time = data.get('response_time_ms', 0)
            assert total_time < 100, f"Health check levou {total_time}ms"
"""

if __name__ == "__main__":
    print("=" * 80)
    print("EXEMPLOS DE INTEGRAÇÃO - HEALTH CHECKS FIMCE")
    print("=" * 80)
    print()
    print("1. Kubernetes Deployment")
    print("2. Docker Compose")
    print("3. Dockerfile com HEALTHCHECK")
    print("4. Nginx Load Balancer")
    print("5. CI/CD Pipeline (GitHub Actions)")
    print("6. Script de Monitoramento Contínuo")
    print("7. Alertas e Notificações")
    print("8. Testes Automatizados")
    print()
    print("Consulte o código acima para cada exemplo específico")
