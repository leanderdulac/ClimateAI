"""
API Router for Climate Capital Charge (CCC) Calculation Service
Implements: CCC = max(0, VaR_99%(Portfólio|evento_climático) - Reservas_climáticas)
Where: Reservas_climáticas = 0.03 × Prêmio_total_portfólio [EIOPA requirement for non-hedgeable risks]
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from services.climate_capital_charge_service import (
    PolicyClimateRisk,
    calculate_climate_capital_charge,
    calculate_climate_reserves,
    calculate_portfolio_climate_var,
    calculate_unmodeled_events_reserve,
    get_unmodeled_events_reserve_range,
    optimize_climate_reserves,
    perform_portfolio_stress_test,
)

router = APIRouter()


@router.post("/climate-capital-charge/calculate")
async def calculate_climate_capital_charge_endpoint(
    policy_ids: List[str] = Query(
        ..., description="List of policy IDs in the portfolio"
    ),
    premium_values: List[float] = Query(
        ..., description="List of premium values for each policy"
    ),
    climate_risk_scores: List[float] = Query(
        ..., description="List of climate risk scores for each policy (0-1 scale)"
    ),
    climate_correlations: List[float] = Query(
        ..., description="List of climate correlations for each policy (0-1 scale)"
    ),
    expected_climate_losses: List[float] = Query(
        ..., description="List of expected climate losses for each policy"
    ),
    climate_var_99_values: List[float] = Query(
        ..., description="List of climate VaR 99% values for each policy"
    ),
    climate_scenario_impacts: List[float] = Query(
        ..., description="List of climate scenario impact factors for each policy"
    ),
    climate_scenario: str = Query(
        "moderate_warming",
        description="Climate scenario: baseline, moderate_warming, severe_warming, extreme_events, transition_shock",
    ),
    stress_level: str = Query(
        "moderate_stress",
        description="Stress level: low_stress, moderate_stress, high_stress, extreme_stress",
    ),
    unmodeled_reserve_rate: float = Query(
        0.045,
        ge=0.03,
        le=0.06,
        description="Additional reserve rate for unmodeled climate events (3-6% of premium)",
    ),
):
    """
    Calculate Climate Capital Charge with additional unmodeled events reserve:
    CCC = max(0, VaR_99%(Portfólio|evento_climático) - (Reservas_climáticas + Reserva_adicional))
    Where:
    - Reservas_climáticas = 0.03 × Prêmio_total_portfólio [EIOPA requirement]
    - Reserva_adicional = 3-6% do prêmio para eventos climáticos não-modelado
    """
    try:
        # Validate input lengths match
        n_policies = len(policy_ids)
        if not all(
            len(lst) == n_policies
            for lst in [
                premium_values,
                climate_risk_scores,
                climate_correlations,
                expected_climate_losses,
                climate_var_99_values,
                climate_scenario_impacts,
            ]
        ):
            raise HTTPException(
                status_code=400, detail="All input lists must have the same length"
            )

        if n_policies == 0:
            raise HTTPException(
                status_code=400, detail="At least one policy is required"
            )

        # Create policy objects
        policies = []
        for i in range(n_policies):
            policy = PolicyClimateRisk(
                policy_id=policy_ids[i],
                premium_value=premium_values[i],
                climate_risk_score=climate_risk_scores[i],
                climate_correlation=climate_correlations[i],
                expected_climate_loss=expected_climate_losses[i],
                climate_var_99=climate_var_99_values[i],
                climate_scenario_impact=climate_scenario_impacts[i],
            )
            policies.append(policy)

        # Calculate climate capital charge with unmodeled events reserve
        result = calculate_climate_capital_charge(
            policies, climate_scenario, stress_level, unmodeled_reserve_rate
        )

        # Calculate individual policy contributions to portfolio risk
        individual_contributions = []
        total_portfolio_premium = sum(premium_values)
        for i, policy in enumerate(policies):
            premium_percentage = (
                policy.premium_value / total_portfolio_premium
                if total_portfolio_premium > 0
                else 0
            )
            expected_loss_percentage = (
                policy.expected_climate_loss / sum(expected_climate_losses)
                if sum(expected_climate_losses) > 0
                else 0
            )
            risk_contribution = policy.climate_risk_score * premium_percentage

            individual_contributions.append(
                {
                    "policy_id": policy.policy_id,
                    "premium_value": policy.premium_value,
                    "premium_percentage": premium_percentage,
                    "climate_risk_score": policy.climate_risk_score,
                    "expected_climate_loss": policy.expected_climate_loss,
                    "expected_loss_percentage": expected_loss_percentage,
                    "risk_contribution_percentage": risk_contribution,
                    "climate_var_99": policy.climate_var_99,
                    "climate_scenario_impact": policy.climate_scenario_impact,
                }
            )

        return {
            "climate_capital_charge": result.climate_capital_charge,
            "portfolio_var_99": result.portfolio_var_99,
            "climate_reserves": result.climate_reserves,  # EIOPA requirement (3%)
            "unmodeled_events_reserve": result.unmodeled_events_reserve,  # Additional reserve (3-6%)
            "total_climate_reserves": result.total_climate_reserves,  # Combined reserves
            "portfolio_premium": result.portfolio_premium,
            "reserve_rate": result.reserve_rate,  # EIOPA reserve rate (0.03)
            "unmodeled_reserve_rate": result.unmodeled_reserve_rate,  # Additional reserve rate (0.03-0.06)
            "climate_scenario_type": result.climate_scenario_type,
            "calculation_method": result.calculation_method,
            "portfolio_size": result.portfolio_size,
            "climate_risk_concentration": result.climate_risk_concentration,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "individual_policy_contributions": individual_contributions,
            "climate_reserves_calculation": {
                "eiopa_reserves": f"{result.reserve_rate*100:.2f}% of total portfolio premium: R$ {result.climate_reserves:,.2f}",
                "unmodeled_events_reserve": f"{result.unmodeled_reserve_rate*100:.2f}% of total portfolio premium: R$ {result.unmodeled_events_reserve:,.2f}",
                "total_reserves": f"Combined reserves: R$ {result.total_climate_reserves:,.2f}",
            },
            "capital_efficiency_ratio": (
                result.climate_capital_charge / result.portfolio_premium
                if result.portfolio_premium > 0
                else 0
            ),
            "reserve_efficiency_ratio": (
                result.total_climate_reserves / result.portfolio_premium
                if result.portfolio_premium > 0
                else 0
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Climate capital charge calculation failed: {str(e)}",
        )


@router.post("/climate-capital-charge/portfolio-var")
async def calculate_portfolio_climate_var_endpoint(
    policy_ids: List[str] = Query(..., description="List of policy IDs"),
    premium_values: List[float] = Query(..., description="List of premium values"),
    climate_risk_scores: List[float] = Query(
        ..., description="List of climate risk scores (0-1)"
    ),
    climate_correlations: List[float] = Query(
        ..., description="List of climate correlations (0-1)"
    ),
    expected_climate_losses: List[float] = Query(
        ..., description="List of expected climate losses"
    ),
    climate_scenario: str = Query(
        "moderate_warming", description="Climate scenario to consider"
    ),
    stress_level: str = Query("moderate_stress", description="Stress test level"),
):
    """
    Calculate portfolio climate VaR at 99% confidence level
    """
    try:
        n_policies = len(policy_ids)
        if not all(
            len(lst) == n_policies
            for lst in [
                premium_values,
                climate_risk_scores,
                climate_correlations,
                expected_climate_losses,
            ]
        ):
            raise HTTPException(
                status_code=400, detail="All input lists must have the same length"
            )

        if n_policies == 0:
            raise HTTPException(
                status_code=400, detail="At least one policy is required"
            )

        # Create policy objects
        policies = []
        for i in range(n_policies):
            policy = PolicyClimateRisk(
                policy_id=policy_ids[i],
                premium_value=premium_values[i],
                climate_risk_score=climate_risk_scores[i],
                climate_correlation=climate_correlations[i],
                expected_climate_loss=expected_climate_losses[i],
                climate_var_99=expected_climate_losses[i]
                * 1.5,  # Placeholder VaR value
                climate_scenario_impact=climate_risk_scores[i],  # Placeholder impact
            )
            policies.append(policy)

        # Calculate portfolio climate VaR
        var_result = calculate_portfolio_climate_var(
            policies, climate_scenario, stress_level
        )

        return {
            "portfolio_var_99": var_result.var_99_portfolio,
            "portfolio_var_95": var_result.var_95_portfolio,
            "expected_shortfall_99": var_result.expected_shortfall_99,
            "portfolio_premium": var_result.portfolio_premium,
            "climate_scenario_type": var_result.climate_scenario_type,
            "calculation_method": var_result.calculation_method,
            "confidence_level": var_result.confidence_level,
            "climate_correlation_factor": var_result.climate_correlation_factor,
            "tail_dependence_parameter": var_result.tail_dependence_parameter,
            "calculation_timestamp": var_result.calculation_timestamp.isoformat(),
            "var_to_premium_ratio": (
                var_result.var_99_portfolio / var_result.portfolio_premium
                if var_result.portfolio_premium > 0
                else 0
            ),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Portfolio climate VaR calculation failed: {str(e)}",
        )


@router.post("/climate-capital-charge/unmodeled-events-reserve")
async def calculate_unmodeled_events_reserve_endpoint(
    total_portfolio_premium: float = Query(
        ..., gt=0, description="Total portfolio premium amount"
    ),
    reserve_rate: float = Query(
        0.045,
        ge=0.03,
        le=0.06,
        description="Reserve rate for unmodeled climate events (3-6% of premium)",
    ),
):
    """
    Calculate additional reserve for unmodeled climate events:
    Reserva_adicional = 3-6% do prêmio para eventos climáticos não-modelado
    """
    try:
        reserve_amount = calculate_unmodeled_events_reserve(
            total_portfolio_premium, reserve_rate
        )

        return {
            "total_portfolio_premium": total_portfolio_premium,
            "unmodeled_events_reserve": reserve_amount,
            "reserve_rate": reserve_rate,
            "reserve_percentage": reserve_rate * 100,
            "reserve_range": "3-6% as specified",
            "calculation_timestamp": datetime.now().isoformat(),
            "requirement": "Additional reserve for unmodeled climate events as per requirement",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unmodeled events reserve calculation failed: {str(e)}",
        )


@router.post("/climate-capital-charge/reserves-calculation")
async def calculate_climate_reserves_endpoint(
    total_portfolio_premium: float = Query(
        ..., gt=0, description="Total portfolio premium amount"
    )
):
    """
    Calculate climate reserves based on EIOPA requirement:
    Reservas_climáticas = 0.03 × Prêmio_total_portfólio
    """
    try:
        reserves = calculate_climate_reserves(total_portfolio_premium)

        return {
            "total_portfolio_premium": total_portfolio_premium,
            "climate_reserves": reserves,
            "reserve_rate": 0.03,  # EIOPA requirement
            "reserve_percentage": 3.0,  # 3%
            "calculation_timestamp": datetime.now().isoformat(),
            "regulatory_compliance_note": "Climate reserves calculated according to EIOPA requirements for non-hedgeable climate risks",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Climate reserves calculation failed: {str(e)}"
        )


@router.post("/climate-capital-charge/stress-test")
async def portfolio_stress_test_endpoint(
    policy_ids: List[str] = Query(..., description="List of policy IDs"),
    premium_values: List[float] = Query(..., description="List of premium values"),
    climate_risk_scores: List[float] = Query(
        ..., description="List of climate risk scores (0-1)"
    ),
    climate_correlations: List[float] = Query(
        ..., description="List of climate correlations (0-1)"
    ),
    expected_climate_losses: List[float] = Query(
        ..., description="List of expected climate losses"
    ),
    baseline_scenario: str = Query("baseline", description="Baseline climate scenario"),
    stress_scenario: str = Query(
        "extreme_events", description="Stress climate scenario"
    ),
    unmodeled_reserve_rate: float = Query(
        0.045,
        ge=0.03,
        le=0.06,
        description="Additional reserve rate for unmodeled climate events (3-6% of premium)",
    ),
):
    """
    Perform stress test comparing baseline vs stressed climate scenarios with unmodeled events reserve
    """
    try:
        n_policies = len(policy_ids)
        if not all(
            len(lst) == n_policies
            for lst in [
                premium_values,
                climate_risk_scores,
                climate_correlations,
                expected_climate_losses,
            ]
        ):
            raise HTTPException(
                status_code=400, detail="All input lists must have the same length"
            )

        if n_policies == 0:
            raise HTTPException(
                status_code=400, detail="At least one policy is required"
            )

        # Create policy objects
        policies = []
        for i in range(n_policies):
            policy = PolicyClimateRisk(
                policy_id=policy_ids[i],
                premium_value=premium_values[i],
                climate_risk_score=climate_risk_scores[i],
                climate_correlation=climate_correlations[i],
                expected_climate_loss=expected_climate_losses[i],
                climate_var_99=expected_climate_losses[i]
                * 1.5,  # Placeholder VaR value
                climate_scenario_impact=climate_risk_scores[i],  # Placeholder impact
            )
            policies.append(policy)

        # Perform stress test with unmodeled events reserve
        stress_result = perform_portfolio_stress_test(
            policies, baseline_scenario, stress_scenario, unmodeled_reserve_rate
        )

        return stress_result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Portfolio stress test failed: {str(e)}"
        )


@router.post("/climate-capital-charge/reserve-optimization")
async def optimize_climate_reserves_endpoint(
    policy_ids: List[str] = Query(..., description="List of policy IDs"),
    premium_values: List[float] = Query(..., description="List of premium values"),
    climate_risk_scores: List[float] = Query(
        ..., description="List of climate risk scores (0-1)"
    ),
    climate_correlations: List[float] = Query(
        ..., description="List of climate correlations (0-1)"
    ),
    expected_climate_losses: List[float] = Query(
        ..., description="List of expected climate losses"
    ),
    climate_scenario: str = Query(
        "moderate_warming", description="Climate scenario to consider"
    ),
    target_climate_capital_charge: float = Query(
        0.0, description="Target climate capital charge"
    ),
    unmodeled_reserve_rate: float = Query(
        0.045,
        ge=0.03,
        le=0.06,
        description="Additional reserve rate for unmodeled climate events (3-6% of premium)",
    ),
):
    """
    Optimize climate reserves to achieve target capital charge including unmodeled events reserve
    """
    try:
        n_policies = len(policy_ids)
        if not all(
            len(lst) == n_policies
            for lst in [
                premium_values,
                climate_risk_scores,
                climate_correlations,
                expected_climate_losses,
            ]
        ):
            raise HTTPException(
                status_code=400, detail="All input lists must have the same length"
            )

        if n_policies == 0:
            raise HTTPException(
                status_code=400, detail="At least one policy is required"
            )

        # Create policy objects
        policies = []
        for i in range(n_policies):
            policy = PolicyClimateRisk(
                policy_id=policy_ids[i],
                premium_value=premium_values[i],
                climate_risk_score=climate_risk_scores[i],
                climate_correlation=climate_correlations[i],
                expected_climate_loss=expected_climate_losses[i],
                climate_var_99=expected_climate_losses[i]
                * 1.5,  # Placeholder VaR value
                climate_scenario_impact=climate_risk_scores[i],  # Placeholder impact
            )
            policies.append(policy)

        # Optimize climate reserves including unmodeled events component
        optimization_result = optimize_climate_reserves(
            policies,
            climate_scenario,
            target_climate_capital_charge,
            unmodeled_reserve_rate,
        )

        return optimization_result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Climate reserves optimization failed: {str(e)}"
        )


@router.get("/climate-capital-charge/info")
async def climate_capital_charge_info():
    """
    Get information about the climate capital charge calculation service
    """
    return {
        "description": "Climate Capital Charge Calculation Service",
        "formula": "CCC = max(0, VaR_99%(Portfólio|evento_climático) - (Reservas_climáticas + Reserva_adicional))",
        "constraints": [
            "Reservas_climáticas = 0.03 × Prêmio_total_portfólio [EIOPA requirement for non-hedgeable risks]",
            "Reserva_adicional = 3-6% do prêmio para eventos climáticos não-modelado",
        ],
        "methodology": "Extended Climate Risk Capital Adequacy Framework",
        "regulatory_compliance": "EIOPA (European Insurance and Occupational Pensions Authority) standards",
        "components": {
            "portfolio_var_99": "Value at Risk at 99% confidence level considering climate events",
            "climate_reserves": "Required reserves at 3% of total portfolio premium (EIOPA requirement)",
            "unmodeled_events_reserve": "Additional reserve at 3-6% of premium for unmodeled climate events",
            "total_climate_reserves": "Combined reserves (EIOPA + unmodeled events)",
            "climate_scenario_risk": "Risk assessment based on different climate scenarios",
        },
        "climate_scenarios": {
            "baseline": "Current climate conditions",
            "moderate_warming": "Gradual temperature increase (1.5-2°C)",
            "severe_warming": "Significant warming (2-3°C)",
            "extreme_events": "Increased frequency/severity of extreme events",
            "transition_shock": "Abrupt policy/economic transitions related to climate",
        },
        "stress_levels": {
            "low_stress": "Minor deviations from baseline",
            "moderate_stress": "Reasonable stress test conditions",
            "high_stress": "Significant stress conditions",
            "extreme_stress": "Extreme stress for scenario testing",
        },
        "features": [
            "Climate VaR calculation at portfolio level",
            "EIOPA compliant reserve calculations (3%)",
            "Additional unmodeled events reserve (3-6%)",
            "Scenario-based stress testing",
            "Climate risk concentration metrics",
            "Reserve optimization capabilities",
            "Individual policy risk contribution analysis",
        ],
        "applications": [
            "Insurance capital adequacy assessment",
            "Climate risk capital allocation",
            "Regulatory compliance reporting",
            "Portfolio optimization under climate risk",
            "Stress testing for climate scenarios",
            "Reserve management optimization",
            "Coverage for unmodeled climate events",
        ],
        "eiopa_compliance_notes": [
            "3% reserve requirement for non-hedgeable climate risks",
            "Climate scenario modeling requirements",
            "Correlation impact considerations",
            "Tail risk assessment for extreme events",
        ],
        "unmodeled_events_reserve_notes": [
            "Additional 3-6% reserve for climate events not captured in models",
            "Default rate of 4.5% (midpoint of 3-6% range)",
            "Rate can be adjusted between 3-6% as needed",
            "Combined with EIOPA reserves for total climate coverage",
        ],
    }
