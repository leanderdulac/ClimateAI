from enum import Enum
from typing import Optional
import asyncio
from datetime import datetime, timedelta
from fastapi import APIRouter
from pydantic import BaseModel
import pandas as pd
import logging

from services.extreme_value_pricing_service import DefensivePricingOrchestrator
from services.openmeteo_service import OpenMeteoService
from services.noaa_service import NOAAService

logger = logging.getLogger(__name__)

# This entire file is created based on the user-provided Python script,
# adapted for a FastAPI router.

router = APIRouter()

# --- CONFIGURAÇÕES E CONSTANTES ---


class PricingConstants:
    LOADING_PCT = 0.35
    RISK_MARGIN_PCT = 0.15
    COST_SUBSCRIPTION_AUTO = 150.00
    COST_SUBSCRIPTION_MANUAL = 450.00
    COST_CLAIMS_PCT = 0.08
    COST_ADMIN_PCT = 0.12
    MIN_PROFIT_MARGIN = 0.02
    MAX_COMBINED_RATIO = 1.05


class DecisionFlow(Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"


# --- MODELOS DE DADOS (Pydantic for FastAPI) ---


class PolicyRequest(BaseModel):
    asset_value: float
    severity_amount: float
    frequency_pct: float
    coverage_period_years: int = 1
    scr_score: float = 0.0
    is_manual_underwriting: bool = False
    location_risk_zone: str = "STANDARD"
    latitude: Optional[float] = -23.55
    longitude: Optional[float] = -46.63


class FinancialBreakdown(BaseModel):
    pure_premium: float
    risk_margin: float
    loadings: float
    total_premium: float
    op_claims_cost: float
    op_admin_cost: float
    op_subscription_cost: float
    total_operational_costs: float
    net_profit: float
    profit_margin_pct: float
    combined_ratio: float


class FractalMetrics(BaseModel):
    hurst_exponent: float
    fractal_dimension: float
    regime: str
    complexity: float

class PricingResult(BaseModel):
    is_approved: bool
    status: str
    rejection_reason: Optional[str]
    financials: FinancialBreakdown
    fractal_metrics: Optional[FractalMetrics] = None
    decision_flow: str


# --- MOTOR DE PRECIFICAÇÃO (SERVICE) ---


class ClimatePricingService:

    def calculate_policy(self, request: PolicyRequest) -> PricingResult:
        rejection = self._check_hard_stops(request)
        if rejection:
            # This is a simplified rejection response builder for clarity
            annual_expected_loss = (request.frequency_pct / 100.0) * min(
                request.severity_amount, request.asset_value
            )
            total_expected_loss = annual_expected_loss * request.coverage_period_years
            financials = FinancialBreakdown(
                pure_premium=total_expected_loss,
                risk_margin=0,
                loadings=0,
                total_premium=0,
                op_claims_cost=0,
                op_admin_cost=0,
                op_subscription_cost=0,
                total_operational_costs=0,
                net_profit=-total_expected_loss,
                profit_margin_pct=-100,
                combined_ratio=1,
            )
            return PricingResult(
                is_approved=False,
                status="REJECTED",
                rejection_reason=rejection,
                financials=financials,
                decision_flow=self._determine_flow(request.scr_score).value,
            )

        flow = self._determine_flow(request.scr_score)

        annual_expected_loss = (request.frequency_pct / 100.0) * min(
            request.severity_amount, request.asset_value
        )
        total_expected_loss = annual_expected_loss * request.coverage_period_years

        flow_loading_factor = self._get_flow_loading(flow)

        pure_premium = total_expected_loss
        base_loadings = pure_premium * PricingConstants.LOADING_PCT
        risk_margin = pure_premium * PricingConstants.RISK_MARGIN_PCT
        extra_flow_loading = pure_premium * flow_loading_factor

        total_premium = pure_premium + base_loadings + risk_margin + extra_flow_loading

        cost_sub = (
            PricingConstants.COST_SUBSCRIPTION_MANUAL
            if request.is_manual_underwriting
            else PricingConstants.COST_SUBSCRIPTION_AUTO
        )
        cost_claims = total_premium * PricingConstants.COST_CLAIMS_PCT
        cost_admin = total_premium * PricingConstants.COST_ADMIN_PCT

        total_op_costs = cost_sub + cost_claims + cost_admin

        net_profit = total_premium - total_expected_loss - total_op_costs

        profit_margin = (net_profit / total_premium) if total_premium > 0 else 0
        combined_ratio = (
            ((total_expected_loss + total_op_costs) / total_premium)
            if total_premium > 0
            else 0
        )

        financials = FinancialBreakdown(
            pure_premium=pure_premium,
            risk_margin=risk_margin,
            loadings=base_loadings + extra_flow_loading,
            total_premium=total_premium,
            op_claims_cost=cost_claims,
            op_admin_cost=cost_admin,
            op_subscription_cost=cost_sub,
            total_operational_costs=total_op_costs,
            net_profit=net_profit,
            profit_margin_pct=profit_margin * 100,
            combined_ratio=combined_ratio,
        )

        is_financially_viable = net_profit > 0

        if not is_financially_viable:
            return PricingResult(
                is_approved=False,
                status="REJECTED",
                rejection_reason=f"Viabilidade Financeira Negativa (Margem: {profit_margin*100:.2f}%)",
                financials=financials,
                decision_flow=flow.value,
            )

        status = "REVIEW" if flow == DecisionFlow.ORANGE else "APPROVED"

        return PricingResult(
            is_approved=True,
            status=status,
            rejection_reason=None,
            financials=financials,
            decision_flow=flow.value,
        )

    def _check_hard_stops(self, request: PolicyRequest) -> Optional[str]:
        if request.scr_score >= 800:
            return "REJEIÇÃO AUTOMÁTICA: SCR Score Crítico (>= 800)"

        if request.asset_value > 10_000_000 and request.scr_score > 700:
            return "REJEIÇÃO AUTOMÁTICA: Ativo de Alto Valor (>10M) com Risco Elevado"

        return None

    def _determine_flow(self, scr: float) -> DecisionFlow:
        if scr < 300:
            return DecisionFlow.GREEN
        if scr < 600:
            return DecisionFlow.YELLOW
        if scr < 800:
            return DecisionFlow.ORANGE
        return DecisionFlow.RED

    def _get_flow_loading(self, flow: DecisionFlow) -> float:
        if flow == DecisionFlow.ORANGE:
            return 0.10
        return 0.0


# --- API ENDPOINT ---


async def _calculate_evt_pricing(request: PolicyRequest) -> Optional[PricingResult]:
    """
    Asynchronous EVT/fractal calculation using real climate data.
    Returns None on failure so caller can fallback to heuristic.
    """
    try:
        om_service = OpenMeteoService()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 2)

        logger.info(
            f"Fetching climate data for pricing: {request.latitude}, {request.longitude}"
        )
        # Note: OpenMeteoService.obter_historico is async
        clima_data = await om_service.obter_historico(
            request.latitude,
            request.longitude,
            start_date,
            end_date,
            variavel="temperature_2m_max",
        )

        if not clima_data:
            return None

        df = pd.DataFrame(
            [{"date": d.data, "temperature": d.temperatura} for d in clima_data]
        )
        df["date"] = pd.to_datetime(df["date"])

        orchestrator = DefensivePricingOrchestrator()
        evt_result = orchestrator.price_contract(
            df,
            asset_value=request.asset_value,
            severity_amount=request.severity_amount,
            frequency_pct=request.frequency_pct,
            duration_years=request.coverage_period_years,
        )

        final_price = evt_result.final_premium
        pure_premium_base = (
            (request.frequency_pct / 100.0)
            * min(request.severity_amount, request.asset_value)
            * request.coverage_period_years
        )

        total_loading = max(0, final_price - pure_premium_base)
        risk_padding = total_loading * 0.4
        loadings = total_loading * 0.6

        cost_sub = (
            PricingConstants.COST_SUBSCRIPTION_MANUAL
            if request.is_manual_underwriting
            else PricingConstants.COST_SUBSCRIPTION_AUTO
        )
        cost_claims = final_price * PricingConstants.COST_CLAIMS_PCT
        cost_admin = final_price * PricingConstants.COST_ADMIN_PCT
        total_op_costs = cost_sub + cost_claims + cost_admin

        net_profit = final_price - pure_premium_base - total_op_costs

        financials = FinancialBreakdown(
            pure_premium=pure_premium_base,
            risk_margin=risk_padding,
            loadings=loadings,
            total_premium=final_price,
            op_claims_cost=cost_claims,
            op_admin_cost=cost_admin,
            op_subscription_cost=cost_sub,
            total_operational_costs=total_op_costs,
            net_profit=net_profit,
            profit_margin_pct=(net_profit / final_price * 100) if final_price > 0 else 0,
            combined_ratio=((pure_premium_base + total_op_costs) / final_price)
            if final_price > 0
            else 0,
        )

        fractal_metrics = None
        if evt_result.fractal_metrics:
            fractal_metrics = FractalMetrics(
                hurst_exponent=evt_result.fractal_metrics.hurst_exponent,
                fractal_dimension=evt_result.fractal_metrics.fractal_dimension,
                regime=evt_result.fractal_metrics.regime,
                complexity=evt_result.fractal_metrics.risk_multiplier,
            )

        status = "APPROVED" if net_profit > 0 else "REVIEW"

        return PricingResult(
            is_approved=True,
            status=status,
            rejection_reason=None
            if net_profit > 0
            else "Lucratividade Marginal em Stress Climático",
            financials=financials,
            fractal_metrics=fractal_metrics,
            decision_flow="EVT_FRACTAL_MODEL",
        )
    except Exception as e:
        logger.error(f"EVT Pricing failed: {e}. Falling back to heuristic.")
        return None


@router.post("/calculate", response_model=PricingResult)
async def calculate_policy_endpoint(request: PolicyRequest) -> PricingResult:
    """
    Calculates proper insurance pricing using:
    1. Real Climate Data (OpenMeteo)
    2. Extreme Value Theory (EVT) for tail risk
    3. Fractal Analysis for market regime
    """
    # Directly await the async EVT calculation
    evt_result = await _calculate_evt_pricing(request)

    if evt_result:
        return evt_result

    pricer = ClimatePricingService()
    return pricer.calculate_policy(request)
