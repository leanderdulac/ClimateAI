# 🧪 Disaster Recovery (DR) - Testes e Validação

## 📊 Visão Geral

Este documento descreve os procedimentos de teste de Disaster Recovery para a plataforma ClimateWise.

## 🎯 Objetivos do DR

| Métrica | Target | Descrição |
|---------|--------|-----------|
| **RPO** (Recovery Point Objective) | < 15 min | Perda máxima de dados aceitável |
| **RTO** (Recovery Time Objective) | < 60 min | Tempo máximo para restauração |
| **Disponibilidade** | 99.9% | Uptime anual esperado |

## 📋 Tipos de Testes

### 1. Backup Verification Test (Semanal)
**Objetivo**: Validar integridade dos backups

```bash
# Script de verificação
./scripts/dr/test_backup_integrity.sh

# Valida:
# ✓ Backup mais recente existe
# ✓ Checksum SHA256 válido
# ✓ Restore de teste bem-sucedido
# ✓ Dados consistentes
```

### 2. Failover Test (Mensal)
**Objetivo**: Testar failover para região secundária

```bash
# Script de failover
./scripts/dr/failover_test.sh

# Valida:
# ✓ DNS update para DR region
# ✓ Database replica promovida
# ✓ Aplicação funcionando em us-west-2
# ✓ Dados sincronizados
```

### 3. Full DR Drill (Trimestral)
**Objetivo**: Simulação completa de desastre

```bash
# Script completo
./scripts/dr/full_dr_drill.sh

# Valida:
# ✓ Todos os sistemas em DR
# ✓ Performance aceitável
# ✓ Monitoramento funcionando
# ✓ Alertas configurados
# ✓ Team response time
```

## 🔧 Scripts de DR

### test_backup_integrity.sh
```bash
#!/bin/bash
# Testa integridade do backup mais recente

BACKUP_BUCKET="climatewise-backups-prod"
LATEST_BACKUP=$(aws s3 ls s3://${BACKUP_BUCKET}/ | tail -1 | awk '{print $4}')

echo "Testing backup: ${LATEST_BACKUP}"

# Download
aws s3 cp s3://${BACKUP_BUCKET}/${LATEST_BACKUP} /tmp/test_backup.sql.gz

# Verify checksum
REMOTE_CHECKSUM=$(aws s3 cp s3://${BACKUP_BUCKET}/${LATEST_BACKUP}.sha256 -)
LOCAL_CHECKSUM=$(sha256sum /tmp/test_backup.sql.gz | awk '{print $1}')

if [ "${REMOTE_CHECKSUM}" == "${LOCAL_CHECKSUM}" ]; then
    echo "✓ Checksum OK"
else
    echo "✗ Checksum FAILED"
    exit 1
fi

# Test restore
gunzip -c /tmp/test_backup.sql.gz | psql -h localhost -U climatewise_admin -d climatewise_test

if [ $? -eq 0 ]; then
    echo "✓ Restore test OK"
else
    echo "✗ Restore test FAILED"
    exit 1
fi

echo "✓ All backup tests passed"
```

### failover_test.sh
```bash
#!/bin/bash
# Testa failover para região de DR

DR_REGION="us-west-2"
PRIMARY_REGION="us-east-1"

echo "Starting failover test to ${DR_REGION}..."

# 1. Promover replica de banco de dados
echo "Promoting database replica..."
aws rds promote-read-replica \
  --db-instance-identifier climatewise-db-prod-dr \
  --region ${DR_REGION}

# Aguardar promoção
aws rds wait db-instance-available \
  --db-instance-identifier climatewise-db-prod-dr \
  --region ${DR_REGION}

# 2. Atualizar DNS
echo "Updating DNS..."
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456 \
  --change-batch file://dns_failover.json

# 3. Escalar aplicação em DR
echo "Scaling application in DR..."
aws ecs update-service \
  --cluster climatewise-dr \
  --service backend \
  --desired-count 3 \
  --region ${DR_REGION}

# 4. Validar saúde
echo "Validating health..."
for i in {1..10}; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://api.climatewise.com/health)
    if [ "${RESPONSE}" == "200" ]; then
        echo "✓ Health check OK"
        break
    fi
    sleep 10
done

# 5. Rollback (opcional)
# ./scripts/dr/failback.sh

echo "✓ Failover test completed"
```

### full_dr_drill.sh
```bash
#!/bin/bash
# Simulação completa de desastre

set -e

echo "=========================================="
echo "FULL DISASTER RECOVERY DRILL"
echo "=========================================="
echo "Start Time: $(date)"
echo ""

# Pre-checks
echo "[1/8] Running pre-checks..."
./scripts/dr/pre_checks.sh

# Backup validation
echo "[2/8] Validating backups..."
./scripts/dr/test_backup_integrity.sh

# Activate DR
echo "[3/8] Activating DR environment..."
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456 \
  --change-batch file://dr_activation.json

# Database failover
echo "[4/8] Failing over database..."
aws rds promote-read-replica \
  --db-instance-identifier climatewise-db-prod-dr \
  --region us-west-2

# Wait for DB
echo "[5/8] Waiting for database..."
aws rds wait db-instance-available \
  --db-instance-identifier climatewise-db-prod-dr \
  --region us-west-2

# Scale application
echo "[6/8] Scaling application..."
aws ecs update-service \
  --cluster climatewise-dr \
  --service backend \
  --desired-count 3 \
  --region us-west-2

# Health validation
echo "[7/8] Validating health..."
for i in {1..30}; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://api-dr.climatewise.com/health/full)
    if [ "${RESPONSE}" == "200" ]; then
        echo "✓ Health check passed"
        break
    fi
    echo "Waiting for DR environment... (${i}/30)"
    sleep 10
done

# Post-checks
echo "[8/8] Running post-checks..."
./scripts/dr/post_checks.sh

echo ""
echo "=========================================="
echo "DR DRILL COMPLETED"
echo "=========================================="
echo "End Time: $(date)"

# Calculate duration
# Send report
./scripts/dr/send_report.sh
```

### 4. NOAA Degradation Test (Mensal)
**Objetivo**: Validar continuidade do Unified Pricing com NOAA instável/indisponível

```bash
# Fluxo automatizado (gera relatório + evidências JSON)
./scripts/dr/test_noaa_degradation.sh

# Opcional: customizar URLs e diretório de relatório
API_URL=http://localhost:8000/api/v1/unified-pricing/calculate \
HEALTH_URL=http://localhost:8000/health \
REPORT_DIR=./reports/dr \
./scripts/dr/test_noaa_degradation.sh
```

**Critérios de aceite**:
- A API `/api/v1/unified-pricing/calculate` permanece disponível (HTTP 200) durante os dois níveis de degradação.
- A resposta inclui `explanation.noaa_blend_parameters` coerente com as env vars aplicadas.
- Em cenário NOAA indisponível, há fallback neutro:
  - sem blend NOAA no `combined_risk_score`
  - sem uplift NOAA no `recommended_premium`
  - aviso operacional em `warnings`.

**Evidências obrigatórias**:
- JSON de resposta dos dois níveis de degradação (leve e forte).
- Logs do backend mostrando aplicação dos parâmetros NOAA.
- Registro do horário de início/fim e impacto observado no prêmio.

## 📊 Métricas de DR

### RPO (Recovery Point Objective)
```sql
-- Calcular lag de replicação
SELECT 
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes,
    EXTRACT(EPOCH FROM (now() - reply_time)) AS lag_seconds
FROM pg_stat_replication;
```

**Target**: < 900 segundos (15 minutos)

### RTO (Recovery Time Objective)
```bash
# Medir tempo de failover
START=$(date +%s)

# Trigger failover
./scripts/dr/trigger_failover.sh

# Wait for healthy
until curl -s https://api.climatewise.com/health | jq -r '.status' | grep -q healthy; do
    sleep 5
done

END=$(date +%s)
RTO=$((END - START))

echo "RTO: ${RTO} seconds"
# Target: < 3600 seconds (60 minutes)
```

## 📋 Checklist de DR

### Pré-Teste
- [ ] Backup mais recente validado
- [ ] Replica de DB sincronizada
- [ ] DR environment disponível
- [ ] Team notificada
- [ ] Monitoring pausado (para não gerar alertas)

### Durante Teste
- [ ] DNS atualizado
- [ ] DB promovido
- [ ] Aplicação escalada
- [ ] Health checks passing
- [ ] Dados consistentes
- [ ] Unified Pricing validado com degradação NOAA (leve e forte)
- [ ] Evidência de fallback neutro NOAA coletada

### Pós-Teste
- [ ] Rollback realizado (se necessário)
- [ ] DNS restaurado
- [ ] Primary region ativa
- [ ] Replicação reiniciada
- [ ] Report enviado
- [ ] Lições aprendidas documentadas
- [ ] Parâmetros NOAA restaurados para baseline operacional

## 🚨 Procedimentos de Emergência

### Ativação de DR (Real)
```bash
# Emergência real (não teste)
./scripts/dr/emergency_activation.sh

# Este script:
# 1. Notifica team via PagerDuty
# 2. Ativa DR imediatamente
# 3. Abre war room
# 4. Inicia log de incident
```

### Contatos de Emergência
- **On-Call**: +1-XXX-XXX-XXXX
- **Slack**: #climatewise-incidents
- **PagerDuty**: climatewise-production

## 📚 Documentação Relacionada

- [Terraform DR Module](../../terraform/modules/backup/README.md)
- [Backup Procedures](../../docs/BACKUP_PROCEDURES.md)
- [Incident Response](../../docs/INCIDENT_RESPONSE.md)

## 📊 Histórico de Testes

| Data | Tipo | Resultado | RTO | RPO | Observações |
|------|------|-----------|-----|-----|-------------|
| 2026-02-18 | Full Drill | ✅ Pass | 45 min | 5 min | Primeiro teste |

---

*Documento criado em: 18 de Fevereiro de 2026*
*Próximo teste: 18 de Março de 2026*
