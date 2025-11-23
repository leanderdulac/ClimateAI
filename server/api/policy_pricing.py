from enum import Enum
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

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


class PricingResult(BaseModel):
    is_approved: bool
    status: str
    rejection_reason: Optional[str]
    financials: FinancialBreakdown
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


@router.post("/calculate", response_model=PricingResult)
async def calculate_policy_endpoint(request: PolicyRequest) -> PricingResult:
    """
    Calculates the full policy premium and financial viability based on input parameters.
    This endpoint encapsulates the core backend pricing logic.
    """
    pricer = ClimatePricingService()
    result = pricer.calculate_policy(request)
    return result
