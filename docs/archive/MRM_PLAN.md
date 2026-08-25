# Model Risk Management (Tier 1 Readiness)

## Objetivos
- Rastrear versões de modelos, dados e hyperparâmetros.
- Monitorar performance, drift e viés.
- Garantir aprovação, explicabilidade e reprodutibilidade.

## Processo
1) **Versionamento**
   - Versionar pesos/artefatos no registry (ex: MLflow ou S3 versionado) com hash, hiperparâmetros e dataset IDs.
   - Registrar commit hash do código + versão do docker/image.
2) **Datasets e lineage**
   - Catalogar datasets com origem, período, filtros e data de extração.
   - Armazenar schemas e checks (nulls, ranges, outliers) em cada ingestão.
3) **Validação pré‑produção**
   - Testes: métricas alvo (MAE/RMSE/Logloss), estabilidade, fairness (KS/PSI), stress (cenários extremos).
   - Explainability: SHAP (global + local) salvo por versão.
   - Aprovação: checklist com sign‑off do responsável de risco/model governance.
4) **Monitoramento em produção**
   - Métricas on‑line: distribuição de features (PSI), qualidade de dados (missing/range), latência de inferência, taxa de erros.
   - Métricas de resultado: sinistralidade observada vs prevista, loss ratio, combined ratio por coorte.
   - Alertas: limites para PSI, drift, queda de acurácia, aumento de latência/erro.
5) **Recalibração**
   - Janela e gatilhos definidos (ex: PSI>0.2 ou queda de AUC > 3pp).
   - Pipeline de retreino com dados mais recentes, revalidação completa e nova aprovação.
6) **Auditoria**
   - Cada release documenta: versão, métricas, datasets, SHAP, owners, data de go‑live.
   - Guardar artefatos por período ≥ 7 anos (ajustar conforme jurisdição).

## Próximas implementações sugeridas
- Adicionar MLflow + bucket versionado para artefatos.
- Coletar SHAP nas rotas de predição do backend e expor no dashboard de auditoria.
- Criar serviço de monitoramento de drift (PSI) agendado e publicar alertas (PagerDuty/Slack).
