"""
Backtesting API Endpoints
Regulatory compliance endpoints for SUSEP, Solvency II, Basel III
"""

import logging
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
import numpy as np

from services.backtesting_service import (
    BacktestingService,
    BacktestResult,
    VaRBacktestReport
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/backtesting", tags=["backtesting"])

# Instância global do serviço
backtest_service = BacktestingService()


# ============================================================================
# Request/Response Models
# ============================================================================

class VaRBacktestRequest(BaseModel):
    """Request para backtesting de VaR"""
    policy_id: str = Field(..., description="ID da apólice")
    historical_losses: List[float] = Field(..., description="Perdas históricas observadas")
    var_predictions: List[float] = Field(..., description="Previsões de VaR")
    confidence_level: float = Field(default=0.95, ge=0.90, le=0.99, description="Nível de confiança")
    start_date: date = Field(..., description="Data inicial do histórico")
    end_date: date = Field(..., description="Data final do histórico")


class VaRBacktestResponse(BaseModel):
    """Resposta de backtesting de VaR"""
    policy_id: str
    rating: str
    regulatory_status: str
    var_95_passed: bool
    var_99_passed: bool
    independence_passed: bool
    total_exceptions: int
    expected_exceptions: int
    exception_ratio: float
    recommendations: List[str]
    timestamp: str


class StressTestRequest(BaseModel):
    """Request para stress test"""
    policy_id: str = Field(..., description="ID da apólice")
    portfolio_data: dict = Field(..., description="Dados do portfólio")
    scenarios: Optional[List[str]] = Field(default=None, description="Cenários específicos")


class StressTestResponse(BaseModel):
    """Resposta de stress test"""
    policy_id: str
    scenarios_tested: int
    results: dict
    max_loss: float
    var_95_stressed: float
    var_99_stressed: float
    timestamp: str


class ValidateHistoryRequest(BaseModel):
    """Request para validação de histórico"""
    start_date: date = Field(..., description="Data inicial")
    end_date: date = Field(..., description="Data final")
    min_years: int = Field(default=10, ge=1, description="Anos mínimos requeridos")


class ValidateHistoryResponse(BaseModel):
    """Resposta de validação de histórico"""
    valid: bool
    years: float
    message: str
    meets_susep_requirement: bool
    meets_solvency_ii_requirement: bool


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/var-backtest", response_model=VaRBacktestResponse)
async def run_var_backtest(request: VaRBacktestRequest):
    """
    Executa backtesting de VaR para validação regulatória
    
    **Requisitos Regulatórios:**
    - SUSEP Circular 562/2015
    - Solvency II
    - Basel III
    
    **Testes Incluídos:**
    - Kupiec POF Test
    - Christoffersen Independence Test
    - VaR 95% e 99%
    
    **Rating:**
    - AAA: Todos testes passaram, ratio < 1.1
    - AA: Todos testes passaram
    - A: VaR 95% e 99% passaram
    - BBB: Apenas VaR 95% passou
    - BB: Nenhum teste passou
    """
    try:
        # Validar histórico mínimo
        years = (request.end_date - request.start_date).days / 365.25
        if years < backtest_service.min_history_years:
            logger.warning(
                f"Histórico de {years:.1f} anos é menor que mínimo de "
                f"{backtest_service.min_history_years} anos"
            )
            # Não bloquear, mas alertar
        
        # Converter para numpy arrays
        losses = np.array(request.historical_losses)
        var_preds = np.array(request.var_predictions)
        
        # Validar tamanhos
        if len(losses) != len(var_preds):
            raise HTTPException(
                status_code=400,
                detail=f"Tamanhos incompatíveis: losses={len(losses)}, var={len(var_preds)}"
            )
        
        if len(losses) < 250:
            raise HTTPException(
                status_code=400,
                detail=f"Mínimo de 250 observações requerido. Atual: {len(losses)}"
            )
        
        # Executar backtesting
        report = backtest_service.generate_var_backtest_report(
            policy_id=request.policy_id,
            historical_losses=losses,
            var_predictions=var_preds
        )
        
        # Log resultado
        logger.info(
            f"Backtest completed for {request.policy_id}: "
            f"rating={report.rating}, status={report.regulatory_status}"
        )
        
        return VaRBacktestResponse(
            policy_id=report.policy_id,
            rating=report.rating,
            regulatory_status=report.regulatory_status,
            var_95_passed=report.var_95.passed,
            var_99_passed=report.var_99.passed,
            independence_passed=report.independence.passed,
            total_exceptions=report.total_exceptions,
            expected_exceptions=report.expected_exceptions,
            exception_ratio=report.exception_ratio,
            recommendations=report.recommendations,
            timestamp=report.generation_timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro em backtesting: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro em backtesting: {str(e)}")


@router.post("/stress-test", response_model=StressTestResponse)
async def run_stress_test(request: StressTestRequest):
    """
    Executa stress test com cenários históricos e hipotéticos
    
    **Cenários Obrigatórios:**
    - 2008 Subprime Crisis
    - 2020 COVID Pandemic
    - Brazil 2015 Recession
    - Extreme Climate Event (100-year)
    """
    try:
        # Converter dados do portfólio
        import pandas as pd
        portfolio_df = pd.DataFrame(request.portfolio_data)
        
        # Selecionar cenários
        scenarios = None
        if request.scenarios:
            scenarios = [
                s for s in backtest_service.stress_scenarios
                if s.name in request.scenarios
            ]
        
        # Executar stress tests
        results = backtest_service.run_stress_test(portfolio_df, scenarios)
        
        # Calcular métricas agregadas
        all_losses = []
        for scenario_results in results.values():
            all_losses.append(scenario_results['total_loss'])
        
        return StressTestResponse(
            policy_id=request.policy_id,
            scenarios_tested=len(results),
            results=results,
            max_loss=max(all_losses) if all_losses else 0,
            var_95_stressed=np.percentile(all_losses, 95) if all_losses else 0,
            var_99_stressed=np.percentile(all_losses, 99) if all_losses else 0,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Erro em stress test: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro em stress test: {str(e)}")


@router.post("/validate-history", response_model=ValidateHistoryResponse)
async def validate_history(request: ValidateHistoryRequest):
    """
    Valida se histórico atende requisitos regulatórios
    
    **Requisitos:**
    - SUSEP: 10 anos mínimos
    - Solvency II: 10 anos mínimos
    - Basel III: 5 anos mínimos
    """
    years = (request.end_date - request.start_date).days / 365.25
    
    valid, message = backtest_service.validate_minimum_history(
        request.start_date,
        request.end_date
    )
    
    return ValidateHistoryResponse(
        valid=valid,
        years=years,
        message=message,
        meets_susep_requirement=years >= 10,
        meets_solvency_ii_requirement=years >= 10
    )


@router.get("/test-methods")
async def get_test_methods():
    """
    Retorna métodos de teste disponíveis
    """
    return {
        "tests": [
            {
                "name": "Kupiec POF Test",
                "type": "proportion_of_failures",
                "null_hypothesis": "Exception rate = expected rate",
                "distribution": "Chi-squared(1)",
                "regulatory_compliance": ["SUSEP", "Solvency II", "Basel III"]
            },
            {
                "name": "Christoffersen Independence Test",
                "type": "independence",
                "null_hypothesis": "Exceptions are independent",
                "distribution": "Chi-squared(1)",
                "regulatory_compliance": ["SUSEP", "Solvency II", "Basel III"]
            },
            {
                "name": "Christoffersen Conditional Coverage Test",
                "type": "conditional_coverage",
                "null_hypothesis": "Correct coverage AND independence",
                "distribution": "Chi-squared(2)",
                "regulatory_compliance": ["SUSEP", "Solvency II", "Basel III"]
            },
            {
                "name": "Stress Testing",
                "type": "scenario_analysis",
                "scenarios": [
                    "2008_subprime_crisis",
                    "2020_covid_pandemic",
                    "brazil_2015_recession",
                    "climate_extreme_event"
                ],
                "regulatory_compliance": ["SUSEP", "Solvency II"]
            }
        ],
        "minimum_history_years": 10,
        "confidence_levels": [0.95, 0.99],
        "significance_level": 0.05
    }


@router.get("/example-data")
async def get_example_data():
    """
    Retorna dados de exemplo para teste
    """
    np.random.seed(42)
    n = 10 * 365  # 10 anos
    
    # Gerar perdas sintéticas
    losses = np.random.lognormal(mean=11, sigma=0.5, size=n)
    
    # Gerar VaR predictions (leviamente conservador)
    var_95 = np.percentile(losses, 95) * np.ones(n) * 1.05
    var_99 = np.percentile(losses, 99) * np.ones(n) * 1.05
    
    return {
        "historical_losses": losses.tolist()[:100],  # Primeiros 100 para exemplo
        "var_95_predictions": var_95.tolist()[:100],
        "var_99_predictions": var_99.tolist()[:100],
        "total_observations": n,
        "expected_exceptions_95": int(n * 0.05),
        "expected_exceptions_99": int(n * 0.01)
    }
