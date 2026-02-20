# Plano de DR e Continuidade (Tier 1)

## Objetivos
- RPO: 15 minutos (banco + artefatos críticos).
- RTO: 60 minutos para API pública e frontend.

## Procedimentos
1) **Backups**
   - Postgres: snapshots incrementais a cada 15 min, retenção 30 dias.
   - Redis/Cache: não crítico (reconstrói).
   - Artefatos de modelo: armazenados em bucket versionado + replicação cross‑region.
   - Config/Secrets: KMS + backup das chaves de recuperação.
2) **Testes de restauração (trimestral)**
   - Restaurar backup mais recente em ambiente isolado.
   - Rodar smoke tests: `/health`, pricing, ML prediction.
   - Validar checksums de artefatos e consistência de schema.
3) **Incidente de indisponibilidade**
   - Acionar war room (Slack/Phone) e registrar no runbook.
   - Alternativa de deploy: usar imagens estáveis pré‑aprovadas, DNS cutover (blue/green) ou fallback CDN para frontend.
4) **Falha de provedor climático**
   - Ativar fallback (NOAA/OpenMeteo/xWeather) via feature flag; forçar cache local.
   - Caso múltiplos provedores falhem, usar dados sintéticos para continuidade do simulador, marcando respostas como FALLBACK.
5) **Recuperação**
   - Restaurar DB para snapshot T‑Δt ≤ 15 min.
   - Recriar serviços via IaC (Terraform) ou docker‑compose, apontar para secrets em KMS.
6) **Pós‑incidente**
   - Post‑mortem em 72h com causas, tempo de detecção, tempo de recuperação e ações CAPA.

## Checklist rápido
- Backup mais recente verificado?
- Secrets disponíveis (KMS) e rotação pós‑incidente planejada?
- DNS/ingress preparado para cutover?
- Alertas e logs ativos após recuperação?
