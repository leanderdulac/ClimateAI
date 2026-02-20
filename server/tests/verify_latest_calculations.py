import asyncio
from api.integrated_pricing_framework import calculate_comprehensive_premium, PolicyPricingInput
from services.comprehensive_pricing_service import comprehensive_pricing_service

async def verify_logs():
    print("--- Verificando Case A (Log: Premium 1636.59) ---")
    # Reconstructing from log: 
    # Frequency: 17% (0.17)
    # Severity: 6418
    # Coverage: 1 year
    # Expected Claims (PTP) = 0.17 * 6418 = 1091.06
    
    ptp_a = 0.17 * 6418
    print(f"PTP Calc: {ptp_a}")
    
    # We need to reverse engineer the specific comprehensive input that yields 1636.59
    # Or just check if 1636.59 is a reasonable markup over 1091.06 (approx 1.5x)
    # The integrated framework defines:
    # Premium = PTP * (1+ML) * (1+TR) * (1+CC) * SupplyDemand
    
    # Let's perform a dry run of the service logic with default params
    input_a = PolicyPricingInput(
        policy_id="CASE_A",
        pure_theoretical_premium=ptp_a,
        loading_margin=0.1, # approx standard
        total_risk_factor=0.05, # approx standard
        climate_change_factor=0.1, # approx standard
        zone_policies_premiums=[],
        free_capital=1000000
    )
    
    result_a = await comprehensive_pricing_service.calculate_comprehensive_pricing(input_a)
    print(f"Simulated Premium A: {result_a.final_premium}")
    print(f"Simulated Break-even: {result_a.final_premium * result_a.cost_breakdown.get('combined_ratio', 1.0)}")
    print(f"Simulated Profit: {result_a.cost_breakdown.get('net_income', 0.0)}")
    
    print("\n--- Verificando Case B (Log: Premium 3639.60) ---")
    # Frequency: 15% (0.15)
    # Severity: 16176
    # PTP = 0.15 * 16176 = 2426.4
    ptp_b = 0.15 * 16176
    print(f"PTP Calc: {ptp_b}")
    
    input_b = PolicyPricingInput(
        policy_id="CASE_B",
        pure_theoretical_premium=ptp_b,
        loading_margin=0.1,
        total_risk_factor=0.05,
        climate_change_factor=0.1,
        zone_policies_premiums=[],
        free_capital=1000000
    )
    result_b = await comprehensive_pricing_service.calculate_comprehensive_pricing(input_b)
    print(f"Simulated Premium B: {result_b.final_premium}")
    print(f"Simulated Profit: {result_b.cost_breakdown.get('net_income', 0.0)}")

    # Actuarial Health Check
    # Combined Ratio should be < 1.0 (or close to it for profitability)
    # Margin should be positive
    
    print("\n--- Conclusão dos Logs do Usuário ---")
    # Case A Logged: Premium 1636.59, Profit 68.21
    margin_a = 68.21 / 1636.59
    print(f"Log Case A Margin: {margin_a:.2%}")
    
    # Case B Logged: Premium 3639.60, Profit 335.28
    margin_b = 335.28 / 3639.60
    print(f"Log Case B Margin: {margin_b:.2%}")

if __name__ == "__main__":
    asyncio.run(verify_logs())
