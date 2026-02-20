# ClimateAI - Tier 1 Implementation Roadmap
## Preparação para Seguradoras Globais

Este documento descreve o plano de implementação dos requisitos necessários para atender seguradoras globais (Tier 1), incluindo compliance com regulamentações internacionais (Solvency II, ORSA, TCFD, ISSB).

---

## ✅ Status Atual (Fevereiro 2026)

### Observabilidade
- [x] OpenTelemetry Collector configurado (`docker-compose.otel.yml`)
- [x] Redaction de PII em logs e traces (`server/middleware/redaction.py`)
- [x] Dashboards SLO no Grafana (`monitoring/grafana/dashboards/slo-overview.json`)
- [x] Regras de alerta Prometheus (`monitoring/prometheus-rules.yml`)
- [x] X-Request-ID propagation front→back (`client/src/lib/requestId.ts`)

### Resiliência
- [x] Circuit Breaker pattern implementado (`server/lib/resilient_http_client.py`)
- [x] Retry com backoff exponencial e jitter
- [x] Timeouts configuráveis por serviço
- [x] Health checks e status de saúde por cliente HTTP

### Segurança
- [x] Rate limiting básico implementado
- [x] Redaction de PII (CPF, CNPJ, email, cartão de crédito, etc.)
- [ ] WAF na borda (pendente: configuração CDN/Ingress)
- [ ] Secrets em secret manager (pendente: AWS Secrets Manager / HashiCorp Vault)

### CI/CD
- [x] Pipeline básico (.github/workflows/ci.yml)
- [x] npm/pip audit bloqueantes
- [ ] SAST/DAST (pendente: SonarQube, Snyk, ou equivalente)
- [ ] SBOM publish (pendente: Syft, CycloneDX)
- [ ] Scan de contêiner (pendente: Trivy, Clair)

---

## 📋 Itens Pendentes por Categoria

### 1. Observabilidade Completa

#### ✅ Implementado
- OTel Collector com configuração completa
- Redaction de PII em logs e traces
- Dashboards de SLO (disponibilidade, latência, error rate)
- X-Request-ID propagation

#### ⏳ Pendente
- [ ] Export para APM de produção (Datadog, New Relic, ou Dynatrace)
- [ ] Configurar sampling probabilístico em produção
- [ ] Implementar métricas customizadas de negócio
- [ ] Runbooks de operação de dashboards

**Arquivos criados:**
- `docker-compose.otel.yml`
- `monitoring/otel-collector-config.yaml`
- `monitoring/prometheus-rules.yml`
- `monitoring/grafana/dashboards/slo-overview.json`

---

### 2. Resiliência e Segurança em Runtime

#### ✅ Implementado
- Circuit Breaker com configuração por serviço
- Retry com backoff exponencial
- Timeouts configuráveis
- Cliente HTTP resiliente unificado

#### ⏳ Pendente
- [ ] Integrar circuit breaker em todos os serviços externos (NOAA, OpenMeteo, Embrapa, xWeather)
- [ ] WAF na borda (Cloudflare, AWS WAF, ou Azure WAF)
- [ ] Rate limiting configurável por rota/tipo de cliente
- [ ] Health checks sintéticos (Pingdom, Uptime Robot, ou equivalente)

**Arquivos criados:**
- `server/lib/resilient_http_client.py`
- `server/middleware/redaction.py` (enhanced)

**Como usar o cliente resiliente:**
```python
from lib.resilient_http_client import create_resilient_client

# Criar cliente para API externa
noaa_client = create_resilient_client(
    service_name="noaa",
    base_url="https://api.noaa.gov",
    api_key=settings.NOAA_API_KEY,
    timeout_seconds=30.0,
    max_retries=3,
)

# Usar em serviços
async def get_weather_data():
    response = await noaa_client.get("/stations")
    return response.json()
```

---

### 3. Schemas Fortes e Contratos

#### ⏳ Pendente
- [ ] Gerar tipos TypeScript do OpenAPI (`npm run api:types`)
- [ ] Eliminar `any` em chamadas HTTP no frontend
- [ ] Pydantic strict mode em todas as rotas
- [ ] Validação de resposta de integrações externas
- [ ] Testes de contrato API front↔back

**Comando para gerar tipos:**
```bash
cd client
npm run api:types  # Gera src/types/api.d.ts do OpenAPI
```

---

### 4. Segurança e Compliance em CI/CD

#### ⏳ Pendente
- [ ] SAST (SonarQube, CodeQL, ou Snyk Code)
- [ ] DAST (OWASP ZAP, ou equivalente)
- [ ] SBOM generation e publish (Syft + CycloneDX)
- [ ] Scan de contêiner (Trivy ou Grype)
- [ ] Branch protection rules no GitHub
- [ ] Code owners para código crítico

**Exemplo de configuração Trivy no CI:**
```yaml
- name: Container Scan (Trivy)
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'ghcr.io/${{ github.repository }}:${{ github.sha }}'
    format: 'sarif'
    output: 'trivy-results.sarif'
```

---

### 5. Model Risk Management (MRM)

#### ⏳ Pendente
- [ ] MLflow para registry de modelos
- [ ] Versionamento de modelos e datasets
- [ ] Lineage de dados e hiperparâmetros
- [ ] Monitoramento de drift (PSI - Population Stability Index)
- [ ] SHAP global/local para explainability
- [ ] Processo de aprovação e revalidação periódica

**Estrutura sugerida:**
```
server/
  models/
    registry/       # MLflow artifacts
    versions/       # Versioned model files
    metadata/       # Model cards e metadata
  monitoring/
    drift/          # PSI calculations
    explainability/ # SHAP values
```

---

### 6. DR/Resiliência (Disaster Recovery)

#### ⏳ Pendente
- [ ] Terraform/IaC para recriar ambientes
- [ ] Backup automatizado (RPO <= 15m)
- [ ] Teste trimestral de restore/DR (RTO <= 60m)
- [ ] Runbook de DR documentado e testado
- [ ] Ambiente isolado para testes de DR

**RPO/RTO Targets:**
- RPO (Recovery Point Objective): 15 minutos
- RTO (Recovery Time Objective): 60 minutos

---

### 7. UX/Compliance

#### ⏳ Pendente
- [ ] Banner de consentimento de dados (LGPD/GDPR)
- [ ] Política de privacidade e termos de uso
- [ ] Masking de PII no frontend
- [ ] Expiração de sessão (timeout de inatividade)
- [ ] Acessibilidade (a11y) validada (WCAG 2.1 AA)
- [ ] Revisão de conteúdo para PII mínima

---

### 8. Integrações e Fallback

#### ⏳ Pendente
- [ ] Caching consistente com Redis para provedores climáticos
- [ ] SLAs por provedor documentados
- [ ] Monitoramento de fallback com alertas
- [ ] Circuit breaker metrics expostas no Prometheus
- [ ] Healthchecks sintéticos por provedor

**Estrutura de caching sugerida:**
```python
from services.cache import cached_with_ttl

@cached_with_ttl(ttl=3600, key_prefix="openmeteo")
async def get_weather_data(lat, lon):
    # Chamada à API externa
    pass
```

---

### 9. Documentação e Runbooks

#### ⏳ Pendente
- [ ] Post-mortem template com CAPA (Corrective Action Preventive Action)
- [ ] Runbooks de incidentes
- [ ] Runbooks de rollbacks
- [ ] Runbooks de feature flags
- [ ] Manual de operação de SLO/SLA
- [ ] Playbooks de escalonamento

**Template de Post-Mortem:**
```markdown
# Post-Mortem: [ID do Incidente]

## Resumo
- Data: [DATA]
- Duração: [DURAÇÃO]
- Severidade: [SEVERIDADE]
- Impacto: [IMPACTO]

## Timeline
- [HH:MM] Detecção
- [HH:MM] Investigação
- [HH:MM] Mitigação
- [HH:MM] Resolução

## Root Cause (5 Whys)
1. Por que...?
2. ...

## CAPA
- Corrective Actions: [...]
- Preventive Actions: [...]

## Lessons Learned
- [...]
```

---

## 🚀 Próximos Passos Imediatos

### Semana 1-2
1. Integrar circuit breaker em todos os serviços externos
2. Configurar WAF/rate limiting na borda
3. Gerar tipos TypeScript do OpenAPI
4. Adicionar SAST no CI/CD

### Semana 3-4
1. Implementar MLflow para registry de modelos
2. Configurar scan de contêiner (Trivy)
3. Implementar caching Redis para APIs externas
4. Criar runbooks de incidentes

### Semana 5-6
1. Teste de DR em ambiente isolado
2. Validação de acessibilidade (a11y)
3. Banner de consentimento LGPD/GDPR
4. Documentação completa de SLO/SLA

---

## 📊 Métricas de Sucesso

| Categoria | Métrica | Target | Status |
|-----------|---------|--------|--------|
| Disponibilidade | Uptime | >= 99.9% | 🟡 |
| Latência | P99 | < 500ms | 🟡 |
| Error Rate | 5xx | < 0.1% | 🟡 |
| RPO | Backup lag | < 15min | ⚪ |
| RTO | Restore time | < 60min | ⚪ |
| Security | Vulnerabilities críticas | 0 | 🟡 |
| Compliance | PII em logs | 0 | ✅ |

Legenda: ✅ Implementado | 🟡 Em progresso | ⚪ Pendente

---

## 📚 Referências

- **Solvency II**: Directive 2009/138/EC
- **ORSA**: Own Risk and Solvency Assessment
- **TCFD**: Task Force on Climate-related Financial Disclosures
- **ISSB**: International Sustainability Standards Board
- **LGPD**: Lei Geral de Proteção de Dados (Lei 13.709/2018)
- **GDPR**: General Data Protection Regulation (EU) 2016/679
- **OpenTelemetry**: https://opentelemetry.io/
- **MLflow**: https://mlflow.org/

---

## 👥 Responsáveis

| Área | Responsável | Revisor |
|------|-------------|---------|
| Observabilidade | Platform Team | Security Team |
| Resiliência | Backend Team | SRE Team |
| Segurança | Security Team | CISO |
| CI/CD | DevOps Team | Platform Team |
| MRM | ML Team | Risk Team |
| DR/BCP | SRE Team | Compliance |
| UX/Compliance | Product Team | Legal |

---

*Última atualização: Fevereiro 2026*
*Versão: 1.0*
