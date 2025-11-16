"""
API Router for Climate Solvency Capital Requirement (SCR) Calculation Service
Implements: SCR_climático = √[ Σ_{i,j} Corr_{i,j} · SCR_i · SCR_j ]
Where: SCR_i = VaR_99.5%(perda_evento_i) - E[perda_evento_i]
And: Corr_{i,j} = 0.25 se i ≠ j  [baixa correlação entre perigos]
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime

from services.climate_scr_service import (
    climate_scr_service,
    calculate_portfolio_scr,
    calculate_simple_portfolio_scr,
    calculate_peril_specific_scr,
    create_correlation_matrix
)

router = APIRouter()

@router.post("/climate-scr/calculate-individual")
async def calculate_individual_scr_endpoint(
    var_995_loss: float = Query(..., gt=0, description="VaR at 99.5% confidence level for the event"),
    expected_loss: float = Query(..., ge=0, description="Expected loss for the event")
):
    """
    Calculate individual SCR component:
    SCR_i = VaR_99.5%(perda_evento_i) - E[perda_evento_i]
    """
    try:
        individual_scr = (var_995_loss - expected_loss)
        individual_scr = max(0, individual_scr)  # Ensure non-negative
        
        return {
            "individual_scr": individual_scr,
            "var_995_loss": var_995_loss,
            "expected_loss": expected_loss,
            "calculation_method": "SCR_i = VaR_99.5% - E[loss]",
            "formula": "SCR_i = VaR_99.5%(perda_evento_i) - E[perda_evento_i]"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Individual SCR calculation failed: {str(e)}")

@router.post("/climate-scr/calculate-portfolio")
async def calculate_portfolio_scr_endpoint(
    var_995_losses: List[float] = Query(..., description="List of VaR 99.5% losses for each event type"),
    expected_losses: List[float] = Query(..., description="List of expected losses for each event type"),
    correlation_matrix: Optional[List[List[float]]] = None
):
    """
    Calculate portfolio-level climate SCR using the correlation-based formula:
    SCR_climático = √[ Σ_{i,j} Corr_{i,j} · SCR_i · SCR_j ]
    Where: SCR_i = VaR_99.5%(perda_evento_i) - E[perda_evento_i]
    And: Corr_{i,j} = 0.25 se i ≠ j [baixa correlação entre perigos]
    """
    try:
        result = calculate_portfolio_scr(var_995_losses, expected_losses, correlation_matrix)
        
        # Calculate diversification benefit
        sum_individual_scrs = sum(result.individual_scrs)
        diversification_benefit = sum_individual_scrs - result.total_scr if sum_individual_scrs > 0 else 0
        
        # Calculate diversification ratio
        diversification_ratio = (diversification_benefit / sum_individual_scrs) if sum_individual_scrs > 0 else 0
        
        return {
            "total_climate_scr": result.total_scr,
            "portfolio_size": result.portfolio_size,
            "individual_scrs": result.individual_scrs,
            "var_995_losses": result.var_995_losses,
            "expected_losses": result.expected_losses,
            "correlation_matrix": result.correlation_matrix,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "diversification_metrics": {
                "sum_of_individual_scrs": sum_individual_scrs,
                "diversification_benefit": diversification_benefit,
                "diversification_ratio": diversification_ratio,
                "diversification_percentage": diversification_ratio * 100
            },
            "formula": "SCR_climático = √[ Σ_{i,j} Corr_{i,j} · SCR_i · SCR_j ]",
            "methodology": {
                "individual_scr_calculation": "SCR_i = VaR_99.5%(perda_evento_i) - E[perda_evento_i]",
                "correlation_structure": "Corr_{i,j} = 0.25 se i ≠ j [baixa correlação entre perigos]",
                "correlation_diagonal": "Corr_{i,i} = 1.0 [perfect self-correlation]"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio SCR calculation failed: {str(e)}")

@router.post("/climate-scr/calculate-simple-portfolio")
async def calculate_simple_portfolio_scr_endpoint(
    var_995_losses: List[float] = Query(..., description="List of VaR 99.5% losses for each event type"),
    expected_losses: List[float] = Query(..., description="List of expected losses for each event type")
):
    """
    Calculate portfolio SCR with default 0.25 correlation between different perils
    Following the exact formula specification:
    - SCR_i = VaR_99.5%(perda_evento_i) - E[perda_evento_i]
    - Corr_{i,j} = 0.25 se i ≠ j
    """
    try:
        result = calculate_simple_portfolio_scr(var_995_losses, expected_losses)
        
        # Calculate diversification benefit
        sum_individual_scrs = sum(result.individual_scrs)
        diversification_benefit = sum_individual_scrs - result.total_scr if sum_individual_scrs > 0 else 0
        diversification_ratio = (diversification_benefit / sum_individual_scrs) if sum_individual_scrs > 0 else 0
        
        return {
            "total_climate_scr": result.total_scr,
            "portfolio_size": result.portfolio_size,
            "individual_scrs": result.individual_scrs,
            "var_995_losses": result.var_995_losses,
            "expected_losses": result.expected_losses,
            "correlation_matrix": result.correlation_matrix,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "diversification_metrics": {
                "sum_of_individual_scrs": sum_individual_scrs,
                "diversification_benefit": diversification_benefit,
                "diversification_ratio": diversification_ratio,
                "diversification_percentage": diversification_ratio * 100
            },
            "default_correlation": 0.25,
            "formula": "SCR_climático = √[ Σ_{i,j} Corr_{i,j} · SCR_i · SCR_j ]",
            "correlation_structure": "Corr_{i,j} = 0.25 se i ≠ j [baixa correlação entre perigos]"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simple portfolio SCR calculation failed: {str(e)}")

@router.post("/climate-scr/calculate-peril-specific")
async def calculate_peril_specific_scr_endpoint(
    peril_losses: Dict[str, Dict[str, float]]
):
    """
    Calculate SCR from peril-specific data with default correlations.
    Input format: {
      "flood": {"var_995": 10000, "expected": 2000},
      "wind": {"var_995": 8000, "expected": 1500},
      ...
    }
    """
    try:
        result = calculate_peril_specific_scr(peril_losses)
        
        # Calculate diversification benefit
        sum_individual_scrs = sum(result.individual_scrs)
        diversification_benefit = sum_individual_scrs - result.total_scr if sum_individual_scrs > 0 else 0
        diversification_ratio = (diversification_benefit / sum_individual_scrs) if sum_individual_scrs > 0 else 0
        
        return {
            "total_climate_scr": result.total_scr,
            "portfolio_size": result.portfolio_size,
            "peril_breakdown": {f"peril_{i}": {
                "name": list(peril_losses.keys())[i] if i < len(peril_losses) else f"peril_{i}",
                "var_995": result.var_995_losses[i],
                "expected_loss": result.expected_losses[i],
                "individual_scr": result.individual_scrs[i]
            } for i in range(result.portfolio_size)},
            "individual_scrs": result.individual_scrs,
            "correlation_matrix": result.correlation_matrix,
            "calculation_timestamp": result.calculation_timestamp.isoformat(),
            "diversification_metrics": {
                "sum_of_individual_scrs": sum_individual_scrs,
                "diversification_benefit": diversification_benefit,
                "diversification_ratio": diversification_ratio,
                "diversification_percentage": diversification_ratio * 100
            },
            "default_correlation": 0.25,
            "formula": "SCR_climático = √[ Σ_{i,j} Corr_{i,j} · SCR_i · SCR_j ]",
            "correlation_structure": "Corr_{i,j} = 0.25 se i ≠ j [baixa correlação entre perigos]"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Peril-specific SCR calculation failed: {str(e)}")

@router.post("/climate-scr/create-correlation-matrix")
async def create_correlation_matrix_endpoint(
    n_events: int = Query(..., ge=1, description="Number of climate events/risk types"),
    correlation_value: float = Query(0.25, ge=0, le=1, description="Correlation value for different events")
):
    """
    Create correlation matrix with specified correlation value between different events.
    Default uses 0.25 as specified in the formula: Corr_{i,j} = 0.25 se i ≠ j
    """
    try:
        matrix = create_correlation_matrix(n_events, correlation_value)
        
        return {
            "correlation_matrix": matrix,
            "matrix_size": n_events,
            "off_diagonal_correlation": correlation_value,
            "diagonal_values": [matrix[i][i] for i in range(n_events)],  # Should all be 1.0
            "formula_reference": "Corr_{i,j} = 0.25 se i ≠ j [baixa correlação entre perigos]",
            "notes": {
                "diagonal_ones": "Self-correlation is always 1.0",
                "symmetric": "Matrix is symmetric",
                "default_value": "0.25 represents low correlation between different perils as specified"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correlation matrix creation failed: {str(e)}")

@router.get("/climate-scr/info")
async def climate_scr_info():
    """
    Get information about the climate SCR calculation service
    """
    return {
        "description": "Climate Solvency Capital Requirement Calculation Service",
        "formula": "SCR_climático = √[ Σ_{i,j} Corr_{i,j} · SCR_i · SCR_j ]",
        "components": {
            "individual_scr": "SCR_i = VaR_99.5%(perda_evento_i) - E[perda_evento_i]",
            "correlation_structure": "Corr_{i,j} = 0.25 se i ≠ j [baixa correlação entre perigos]",
            "self_correlation": "Corr_{i,i} = 1.0 (perfect correlation with self)"
        },
        "methodology": "Correlation-based climate risk aggregation following Solvency II principles",
        "regulatory_alignment": "Consistent with Solvency II and climate risk regulatory frameworks",
        "features": [
            "Individual SCR calculation (VaR_99.5% - Expected Loss)",
            "Portfolio-level aggregation using correlation matrix",
            "Default 0.25 correlation between different perils",
            "Diversification benefit quantification",
            "Peril-specific analysis capabilities",
            "Custom correlation matrix support"
        ],
        "applications": [
            "Insurance company climate capital requirements",
            "Climate risk portfolio aggregation",
            "Diversification analysis",
            "Regulatory compliance reporting",
            "Climate risk stress testing",
            "Reinsurance treaty optimization"
        ],
        "default_parameters": {
            "correlation_between_perils": 0.25,  # As specified in the formula
            "confidence_level": 0.995,  # VaR 99.5%
            "minimum_correlation": 0.0,
            "maximum_correlation": 1.0
        },
        "calculation_notes": [
            "SCR components represent the additional capital needed beyond expected losses",
            "Correlation structure represents low dependence between different climate perils",
            "Positive diversification effects reduce total required capital",
            "Formula follows quadratic form for proper risk aggregation"
        ]
    }