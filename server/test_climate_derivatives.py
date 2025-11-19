#!/usr/bin/env python3
"""
Script de Demonstração do Sistema de Precificação de Derivativos Climáticos
FIMCE - Framework Integrado de Modelagem Climático-Econômica
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from services.climate_derivative_pricer import ClimateDerivativePricer


def main():
    print("🚀 FIMCE - Sistema de Precificação de Derivativos Climáticos")
    print("=" * 60)

    # Inicializar pricer
    pricer = ClimateDerivativePricer()

    # Cenário 1: Base
    print("\n📊 Cenário Base (2025)")
    result_base = pricer.price_climate_derivative(
        target_year=2025, iam_adjustment=0.5, scenario_name="Cenário Base"
    )

    print(f"CDD Médio Projetado: {result_base['cdd_analysis']['average_cdd']:.2f}")
    print(f"Temperatura Média: {result_base['temperature_projection']['mean']:.2f}°F")
    print(f"Pagamento Esperado: ${result_base['risk_metrics']['expected_payout']:,.2f}")
    print(f"Preço Bid: ${result_base['pricing']['bid_price']:,.2f}")
    print(f"Preço Ask: ${result_base['pricing']['ask_price']:,.2f}")
    print(f"Spread: ${result_base['pricing']['spread']:,.2f}")
    print(f"VaR (95%): ${result_base['risk_metrics']['var_95']:,.2f}")
    print(f"CVaR (95%): ${result_base['risk_metrics']['cvar_95']:,.2f}")

    # Cenário 2: Quente (+2°F)
    print("\n🔥 Cenário Quente (+2°F)")
    result_hot = pricer.price_climate_derivative(
        target_year=2025,
        iam_adjustment=2.5,  # +2°F adicional
        scenario_name="Cenário Quente",
    )

    print(f"CDD Médio Projetado: {result_hot['cdd_analysis']['average_cdd']:.2f}")
    print(f"Temperatura Média: {result_hot['temperature_projection']['mean']:.2f}°F")
    print(f"Pagamento Esperado: ${result_hot['risk_metrics']['expected_payout']:,.2f}")
    print(f"Preço Bid: ${result_hot['pricing']['bid_price']:,.2f}")
    print(f"Preço Ask: ${result_hot['pricing']['ask_price']:,.2f}")

    # Cenário 3: Volátil
    print("\n🌪️ Cenário Volátil (Maior Variabilidade)")
    result_volatile = pricer.price_climate_derivative(
        target_year=2025, iam_adjustment=0.5, scenario_name="Cenário Volátil"
    )

    print(f"CDD Médio Projetado: {result_volatile['cdd_analysis']['average_cdd']:.2f}")
    print(
        f"Temperatura Média: {result_volatile['temperature_projection']['mean']:.2f}°F"
    )
    print(
        f"Pagamento Esperado: ${result_volatile['risk_metrics']['expected_payout']:,.2f}"
    )
    print(f"Preço Bid: ${result_volatile['pricing']['bid_price']:,.2f}")
    print(f"Preço Ask: ${result_volatile['pricing']['ask_price']:,.2f}")

    # Comparação de Cenários
    print("\n📈 Comparação de Cenários")
    scenarios = [
        {
            "target_year": 2025,
            "iam_adjustment": 0.5,
            "months_to_expiry": 3,
            "scenario_name": "Base",
        },
        {
            "target_year": 2025,
            "iam_adjustment": 2.5,
            "months_to_expiry": 3,
            "scenario_name": "Quente",
        },
        {
            "target_year": 2025,
            "iam_adjustment": 0.5,
            "months_to_expiry": 3,
            "scenario_name": "Volátil",
        },
    ]

    comparison = pricer.compare_scenarios(scenarios)

    print(
        f"{'Cenário':<10} {'CDD Médio':<12} {'Preço Bid':<12} {'Preço Ask':<12} {'VaR 95%':<12}"
    )
    print("-" * 60)
    scenario_names = ["Base", "Quente", "Volátil"]
    for i, data in enumerate(comparison):
        name = scenario_names[i]
        cdd = data["cdd_analysis"]["average_cdd"]
        bid = data["pricing"]["bid_price"]
        ask = data["pricing"]["ask_price"]
        var95 = data["risk_metrics"]["var_95"]
        print(f"{name:<10} {cdd:<12.2f} ${bid:<11,.0f} ${ask:<11,.0f} ${var95:<11,.0f}")

    # Análise de Sensibilidade
    print("\n🔍 Análise de Sensibilidade (±1°F)")
    sensitivity = result_base["sensitivity_analysis"]

    print(f"{'ΔT (°F)':<8} {'Preço Bid':<12} {'Preço Ask':<12} {'VaR 95%':<12}")
    print("-" * 45)
    for delta, data in sensitivity.items():
        bid = data["bid_price"]
        ask = data["ask_price"]
        var95 = data["var_95"]
        print(f"{delta:<8.1f} ${bid:<11,.0f} ${ask:<11,.0f} ${var95:<11,.0f}")

    # Simulação MVP
    print("\n💰 Simulação MVP ($10M Capital)")
    capital = 10_000_000  # Aumentado para $10M para comprar contratos significativos
    ask_price = result_base["pricing"]["ask_price"]
    spread = result_base["pricing"]["spread"]
    cdd_base = result_base["cdd_analysis"]["average_cdd"]
    cdd_hot = result_hot["cdd_analysis"]["average_cdd"]

    for cdd, scenario in [(cdd_base, "Base"), (cdd_hot, "Quente")]:
        contracts = capital / ask_price
        cdd_realized = cdd * contracts
        payout = cdd_realized * pricer.payout_per_cdd
        total_spread = spread * contracts
        holders = payout + (total_spread * 0.5)
        staking = total_spread * 0.3
        team = total_spread * 0.2

        print(f"\nCenário {scenario}:")
        print(f"Contratos Comprados: {contracts:.4f}")
        print(f"CDD Realizado: {cdd_realized:.2f}")
        print(f"Pagamento Total: ${payout:,.2f}")
        print(f"Spread Total: ${total_spread:,.2f}")
        print(f"Retorno para Holders: ${holders:,.2f}")
        print(f"Recompensas Staking: ${staking:,.2f}")
        print(f"Fundo Equipe/ESG: ${team:,.2f}")
        print(f"Retorno Total: {total_spread/capital*100:.2f}%")

    # Validação com INMET (exemplo)
    print("\n🌡️ Validação com Dados INMET")
    try:
        # Exemplo: Estação A701 (São Paulo), Março 2025
        temp_real = pricer.get_inmet_data("A701", "2025-03-01", "2025-03-31")
        if temp_real:
            threshold = 28.0  # °C
            payout_inmet = 10000 if temp_real > threshold else 0
            print(f"Temperatura Real (INMET): {temp_real:.2f}°C")
            print(f"Limiar: {threshold:.1f}°C")
            print(f"Payout: R$ {payout_inmet}")
            print(f"Derivativo Acionado: {'Sim' if temp_real > threshold else 'Não'}")
        else:
            print("Dados INMET não disponíveis (usando dados simulados)")
    except Exception as e:
        print(f"Erro na validação INMET: {e}")

    print("\n✅ Demonstração concluída!")
    print("📋 APIs disponíveis:")
    print("  POST /api/v1/modelagem/derivativos-climaticos/preco")
    print("  POST /api/v1/modelagem/derivativos-climaticos/comparar-cenarios")
    print("  GET /api/v1/modelagem/derivativos-climaticos/analise-risco")
    print("  GET /api/v1/modelagem/derivativos-climaticos/validacao-inmet")


if __name__ == "__main__":
    main()
