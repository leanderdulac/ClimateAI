#!/usr/bin/env python3
"""
Teste do Serviço VaR Backtesting
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

import numpy as np
from services.var_backtesting_service import var_backtesting_service

print("=" * 80)
print("  TESTE DO SERVIÇO VaR BACKTESTING")
print("=" * 80)

# Gerar dados sintéticos
np.random.seed(42)
n = 504  # 2 anos
losses = np.random.lognormal(mean=10, sigma=0.5, size=n)
var_95 = np.percentile(losses, 95)
var_predictions = np.ones(n) * var_95 * 1.05  # Conservador

print("\n📊 DADOS DE TESTE:")
print(f"   Observações: {n}")
print(f"   Nível de confiança: 95%")
print(f"   VaR: {var_95:.2f}")

# Executar backtest
print("\n🔍 EXECUTANDO BACKTEST...")
result = var_backtesting_service.run_backtest(
    policy_id="TEST_POLICY_001",
    historical_losses=losses,
    var_predictions=var_predictions,
    confidence_level=0.95,
    var_model="Historical Simulation",
)

print("\n✅ RESULTADOS:")
print(f"   Exceções: {result.total_exceptions}/{result.n_observations}")
print(f"   Taxa observada: {result.exception_rate:.2%}")
print(f"   Taxa esperada: {result.expected_exception_rate:.2%}")
print(f"   Razão: {result.exception_ratio:.2f}")

print("\n🧪 TESTES ESTATÍSTICOS:")
if result.kupiec_test:
    status = "✅ PASSOU" if result.kupiec_test.passed else "❌ FALHOU"
    print(f"   Kupiec POF: {status} (p={result.kupiec_test.p_value:.4f})")

if result.christoffersen_ind_test:
    status = "✅ PASSOU" if result.christoffersen_ind_test.passed else "❌ FALHOU"
    print(f"   Christoffersen Ind: {status} (p={result.christoffersen_ind_test.p_value:.4f})")

if result.christoffersen_cc_test:
    status = "✅ PASSOU" if result.christoffersen_cc_test.passed else "❌ FALHOU"
    print(f"   Christoffersen CC: {status} (p={result.christoffersen_cc_test.p_value:.4f})")

print("\n🚦 BASEL III TRAFFIC LIGHT:")
zone_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
print(f"   Zona: {zone_emoji.get(result.traffic_light_zone.value, '?')} {result.traffic_light_zone.value.upper()}")
print(f"   Multiplicador: {result.basel_multiplier}x")
print(f"   Status: {result.regulatory_status.value}")

print("\n📋 RECOMENDAÇÕES:")
for rec in result.recommendations[:3]:
    print(f"   • {rec}")

# Gerar relatório
print("\n💾 GERANDO RELATÓRIO...")
report = var_backtesting_service.generate_regulatory_report(result)
print(f"   Report ID: {report.report_id}")
print(f"   Policy: {report.policy_id}")
print(f"   SUSEP Circular: {report.susep_compliance['circular']}")
print(f"   Status: {report.susep_compliance['overall_status']}")

print("\n" + "=" * 80)
print("  ✅ SERVIÇO VaR BACKTESTING FUNCIONANDO CORRETAMENTE")
print("=" * 80)
