# Scripts de Verificação e Testes Manuais

Este diretório contém scripts pontuais de verificação, testes de integração manuais e ferramentas de diagnóstico criados durante o desenvolvimento e validação das diferentes etapas do FIMCE / ClimateWise.

## Execução

Para executar qualquer um dos scripts Python com o ambiente virtual do projeto ativo:

```bash
../../.venv/bin/python <nome_do_script>.py
```

## Categorias

- **Modelagem Atuarial e Risco**: `test_bayesian_bootstrap.py`, `test_climate_risk_modeling.py`, `test_extreme_value_analysis.py`, `test_var_service.py`
- **APIs e Integrações Externas**: `test_noaa_integration.py`, `test_noaa_fallback.py`, `test_grok_specialist.py`, `test_localizacao_automatica.py`
- **Tokenização e Oráculos**: `test_parametric_insurance.py`, `test_pricing_validation.js`
- **Pipelines e Diagnósticos de Deploy**: `verify_apis.sh`, `validate_stage8.sh`, `verify_stage5.sh`, `test_full_platform.sh`
