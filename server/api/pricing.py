"""
Pricing Router - Endpoints para cálculo de pricing de seguros
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.audit_service import log_operation
from services.dynamic_insurance_analysis_service import dynamic_analysis_service

logger = logging.getLogger(__name__)

router = APIRouter()


class PricingRequest(BaseModel):
    """Modelo de requisição para cálculo de pricing"""

    location_id: str
    coverage_amount: float
    coverage_period: int = 1  # em anos
    user_id: Optional[str] = None
    session_id: Optional[str] = None


def calculate_pricing(request: PricingRequest) -> Dict[str, Any]:
    """
    Calcula preço de seguro baseado em dados climáticos e fatores de risco
    Incorpora análise dinâmica de lucratividade e otimização de portfólio
    """
    from services.clima_service import ClimaService
    from services.previsao_service import PrevisaoService

    clima_service = ClimaService()
    previsao_service = PrevisaoService()

    try:
        # Obter dados históricos para análise de risco
        historico_inicio = datetime.now() - timedelta(days=365)
        historico_fim = datetime.now()

        # Obter dados reais de clima para análise de risco
        dados_clima = clima_service.obter_historico(
            latitude=-23.5507,
            longitude=-46.6339,
            data_inicio=historico_inicio,
            data_fim=historico_fim,
        )

        # Calcular fatores de risco com base nos dados históricos
        climatic_risk = 0.0
        economic_risk = 0.2
        location_risk = 0.3

        if dados_clima:
            # Análise da variabilidade climática
            temps = [d.temperatura for d in dados_clima if d.temperatura is not None]
            precip = [d.precipitacao for d in dados_clima if d.precipitacao is not None]

            if temps:
                temp_variability = (
                    np.std(temps) / np.mean(temps) if np.mean(temps) != 0 else 0
                )
                climatic_risk = min(1.0, temp_variability * 2)

            if precip:
                precip_variability = (
                    np.std(precip) / np.mean(precip) if np.mean(precip) != 0 else 0
                )
                climatic_risk = max(climatic_risk, min(1.0, precip_variability * 1.5))

        risk_factors = {
            "climatic_risk": climatic_risk,
            "economic_risk": economic_risk,
            "location_risk": location_risk,
        }

        # Calcular prêmio dinâmico
        dynamic_pricing_result = dynamic_analysis_service.calculate_dynamic_premium(
            coverage_amount=request.coverage_amount,
            risk_factors=risk_factors,
            base_loading_factor=0.20,
        )

        return {
            "final_price": dynamic_pricing_result["final_premium"],
            "expected_claims": dynamic_pricing_result["expected_claims"],
            "profit": dynamic_pricing_result["profit"],
            "profit_margin": dynamic_pricing_result["profit_margin"],
            "break_even_premium": dynamic_pricing_result["break_even_premium"],
            "risk_score": (climatic_risk + economic_risk + location_risk) / 3,
            "risk_factors": risk_factors,
            "is_profitable": dynamic_pricing_result["is_profitable"],
            "recommendations": [
                f"Margem de lucro esperada: {dynamic_pricing_result['profit_margin']:.1%}",
                f"Prêmio mínimo para equilíbrio: R$ {dynamic_pricing_result['break_even_premium']:,.2f}",
                (
                    "Considerar cobertura adicional contra inundações"
                    if climatic_risk > 0.5
                    else ""
                ),
                (
                    "Avaliar período de cobertura mais longo"
                    if request.coverage_period == 1
                    else ""
                ),
            ],
            "compliance_flags": [],
        }
    except Exception as e:
        logger.error(f"Error in enhanced pricing calculation: {str(e)}")
        # Fallback para cálculo original
        return {
            "final_price": request.coverage_amount * 0.05,
            "risk_score": 0.3,
            "risk_factors": {
                "climatic_risk": 0.4,
                "economic_risk": 0.2,
                "location_risk": 0.3,
            },
            "recommendations": [
                "Considerar cobertura adicional contra inundações",
                "Avaliar período de cobertura mais longo",
            ],
            "compliance_flags": [],
            "error": f"Fallback pricing used due to error: {str(e)}",
        }


@router.post("/calculate")
async def calculate_pricing_endpoint(request: PricingRequest) -> Dict[str, Any]:
    """
    Calcular preço de seguro baseado em dados climáticos e fatores de risco

    Args:
        request: Dados da solicitação de pricing

    Returns:
        Resultado do cálculo de pricing com recomendações
    """
    try:
        result = calculate_pricing(request)

        # Registrar operação de auditoria
        audit_id = log_operation(
            operation="pricing_calculation",
            resource_type="insurance_policy",
            action="calculate",
            status="success",
            user_id=request.user_id,
            session_id=request.session_id,
            resource_id=f"location_{request.location_id}",
            details={
                "location_id": request.location_id,
                "coverage_period": request.coverage_period,
                "coverage_amount": request.coverage_amount,
                "risk_factors": result.get("risk_factors", {}),
                "final_price": result.get("final_price", 0),
            },
            risk_score=result.get("risk_score", 0),
            compliance_flags=result.get("compliance_flags", []),
        )

        result["audit_id"] = audit_id
        return result
    except Exception as e:
        # Registrar erro de auditoria
        log_operation(
            operation="pricing_calculation",
            resource_type="insurance_policy",
            action="calculate",
            status="error",
            user_id=getattr(request, "user_id", None),
            session_id=getattr(request, "session_id", None),
            details={"error": str(e)},
            compliance_flags=["calculation_error"],
        )
        logger.error(f"Erro no cálculo de pricing: {e}")
        raise HTTPException(status_code=500, detail=f"Erro cálculo: {str(e)}")
