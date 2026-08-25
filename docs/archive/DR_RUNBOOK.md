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
    - Para o Unified Pricing, validar parâmetros operacionais NOAA no ambiente:
       - `NOAA_RISK_BLEND_WEIGHT` (padrão `0.15`, faixa `0.0..1.0`)
       - `NOAA_PREMIUM_MAX_IMPACT` (padrão `0.12`, faixa `0.0..0.5`)
    - Durante incidente com NOAA instável, reduzir exposição operacional do ajuste meteorológico:
       - Passo 1 (degradação leve): `NOAA_RISK_BLEND_WEIGHT=0.10` e `NOAA_PREMIUM_MAX_IMPACT=0.08`
       - Passo 2 (degradação forte): `NOAA_RISK_BLEND_WEIGHT=0.00` e `NOAA_PREMIUM_MAX_IMPACT=0.00`
    - Confirmar em logs/telemetria que o fallback neutro está ativo (sem blend NOAA no risco e sem uplift NOAA no prêmio).
    - Abrir ticket de reativação controlada para retorno gradual (ex.: +0.05 por etapa após estabilização).
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
- Parâmetros NOAA do Unified Pricing revisados para o estado do incidente?
- Evidência de fallback neutro NOAA anexada ao incidente (logs/trace/response)?
