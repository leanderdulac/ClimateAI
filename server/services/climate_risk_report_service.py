"""
Climate Risk Analysis Report Generator
Implements comprehensive policy analysis reports in the format specified:
RISCO CLIMÁTICO: ALTO (SCR = 680/1000)
├─ Risco físico (inundação): 420 pts [→ 180% até 2050]
├─ Risco transição: 190 pts [CarbonTax R$ 8.400/ano]
└─ Mitigação ativa: -70 pts [medidas detectadas: drenagem, sensores]

DECISÃO: CONDICIONADA (requer sistema de bombeamento)
PRÊMIO: R$ 2.847/ano (vs. R$ 1.200 padrão)

ANÁLISE COMPONENTES:
├─ Perda esperada: R$ 1.050
├─ Carreg. segurança: R$ 315 (CS=30%)
├─ Carreg. contingência: R$ 189 (CCC=18%)
├─ Margem emissor: R$ 378 (ML=18%)
├─ Retorno inv.: R$ 142 (TR=5%)
├─ Carreg. cliente: R$ 569 (CC=20%)
├─ Ajuste capacidade: R$ 204 (concentração zona = 22%)

OPORTUNIDADES DE DESCONTO:
├─ Instalar sistema de drenagem avançado: -R$ 427/ano
└─ Adotar monitoramento IoT: -R$ 142/ano
   PRÊMIO POTENCIAL: R$ 2.278/ano

ALERTAS:
⚠️ Zona com projeção de aumento de sinistralidade 129% até 2050
⚠️ Recomenda-se cobertura complementar de perda de renda
⚠️ Resseguro automático: 40% quota-share ativado

PRÓXIMA REVISÃO: Automática em 12 meses ou se ΔT regional > 1.5°C
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


@dataclass
class PolicyAnalysisReport:
    """Complete climate risk analysis report for a policy"""

    policy_id: str
    risk_level: str
    scr_score: float
    climate_risk_breakdown: Dict[str, Any]
    decision: str
    decision_reason: str
    final_premium: float
    standard_premium: float
    component_analysis: Dict[str, Any]
    discount_opportunities: List[Dict[str, Any]]
    potential_premium: float
    alerts: List[str]
    next_review_date: datetime
    calculation_timestamp: datetime


@dataclass
class ClimateRiskComponents:
    """Risk components for analysis"""

    physical_risk: float
    transition_risk: float
    concentration_risk: float
    mitigation_effect: float
    expected_claims: float


@dataclass
class PremiumBreakdown:
    """Breakdown of premium components"""

    expected_loss: float
    security_loading: float
    contingency_loading: float
    margin_loading: float
    investment_return: float
    climate_change_loading: float
    capacity_adjustment: float


class ClimateRiskReportService:
    """
    Generates comprehensive climate risk analysis reports in the specified format
    """

    def __init__(self):
        # Risk level thresholds
        self.risk_thresholds = {
            "very_low": (0, 200),
            "low": (200, 400),
            "moderate": (400, 600),
            "high": (600, 800),
            "critical": (800, float("inf")),
        }

        # Default component weights
        self.component_weights = {
            "security_loading_rate": 0.30,  # CS = 30% (Carreg. segurança)
            "contingency_loading_rate": 0.18,  # CCC = 18% (Carreg. contingência)
            "margin_loading_rate": 0.18,  # ML = 18% (Margem emissor)
            "investment_return_rate": 0.05,  # TR = 5% (Retorno inv.)
            "climate_change_rate": 0.20,  # CC = 20% (Carreg. cliente)
            "capacity_adjustment_rate": 0.12,  # For capacity/zonal adjustments
        }

        # Discount opportunities catalog
        self.discount_opportunities = {
            "advanced_drainage_system": {
                "name": "Instalar sistema de drenagem avançado",
                "description": "Install advanced drainage system",
                "discount_percentage": 0.15,  # 15% discount
                "discount_amount": 427.0,  # R$ 427/ano
                "implementation_cost": 15000.0,
                "payback_period_months": 36,
                "mitigation_type": "drainage",
            },
            "iot_monitoring": {
                "name": "Adotar monitoramento IoT",
                "description": "Adopt IoT monitoring system",
                "discount_percentage": 0.05,  # 5% discount
                "discount_amount": 142.0,  # R$ 142/ano
                "implementation_cost": 3000.0,
                "payback_period_months": 24,
                "mitigation_type": "monitoring",
            },
            "structural_resistance_upgrade": {
                "name": "Melhorar resistência estrutural",
                "description": "Upgrade structural resistance measures",
                "discount_percentage": 0.10,  # 10% discount
                "discount_amount": 285.0,  # R$ 285/ano
                "implementation_cost": 8000.0,
                "payback_period_months": 32,
                "mitigation_type": "structural",
            },
            "vegetation_cover_improvement": {
                "name": "Aumentar cobertura vegetal",
                "description": "Increase vegetation coverage around property",
                "discount_percentage": 0.03,  # 3% discount
                "discount_amount": 85.0,  # R$ 85/ano
                "implementation_cost": 2500.0,
                "payback_period_months": 34,
                "mitigation_type": "vegetation",
            },
            "refuge_system_installation": {
                "name": "Instalar sistema de refúgio",
                "description": "Install refuge and evacuation system",
                "discount_percentage": 0.07,  # 7% discount
                "discount_amount": 199.0,  # R$ 199/ano
                "implementation_cost": 5000.0,
                "payback_period_months": 30,
                "mitigation_type": "safety",
            },
        }

        # Decision thresholds
        self.decision_thresholds = {
            "approve": 600,  # Approve if SCR < 600
            "condition": 750,  # Condition if 600 ≤ SCR < 750
            "reject": 800,  # Reject if SCR ≥ 800
        }

    def generate_policy_analysis_report(
        self,
        policy_id: str,
        risk_components: ClimateRiskComponents,
        expected_claims: float,
        coverage_amount: float,
        zone_concentration: float = 0.22,
        climate_projections: Optional[Dict[str, float]] = None,
        implemented_mitigation_measures: Optional[List[str]] = None,
        mitigation_impact: Optional[Dict[str, float]] = None,
    ) -> PolicyAnalysisReport:
        """
        Generate comprehensive climate risk analysis report

        Args:
            policy_id: Policy identifier
            risk_components: Climate risk components (physical, transition, concentration, mitigation)
            expected_claims: Expected claims amount
            coverage_amount: Coverage amount
            zone_concentration: Concentration in the zone (0-1)
            climate_projections: Climate projections for the area
            implemented_mitigation_measures: List of already implemented mitigation measures
            mitigation_impact: Impact of implemented mitigation measures

        Returns:
            PolicyAnalysisReport with complete analysis
        """
        if climate_projections is None:
            climate_projections = {
                "temperature_increase_2050": 1.8,
                "risk_increase_percentage": 129.0,
                "year": 2050,
            }

        if implemented_mitigation_measures is None:
            implemented_mitigation_measures = []

        if mitigation_impact is None:
            mitigation_impact = {"points_reduction": 0, "measures_list": []}

        # Determine risk level based on SCR score
        risk_level = self._get_risk_level(risk_components.scr_score)

        # Calculate premium breakdown
        premium_breakdown = self._calculate_premium_breakdown(
            expected_claims, risk_components.scr_score, zone_concentration
        )

        # Calculate total premium
        total_premium = (
            premium_breakdown.expected_loss
            + premium_breakdown.security_loading
            + premium_breakdown.contingency_loading
            + premium_breakdown.margin_loading
            + premium_breakdown.investment_return
            + premium_breakdown.climate_change_loading
            + premium_breakdown.capacity_adjustment
        )

        # Determine decision based on SCR score
        decision, decision_reason = self._determine_policy_decision(
            risk_components.scr_score, implemented_mitigation_measures
        )

        # Generate discount opportunities
        discount_opportunities = self._generate_discount_opportunities(
            total_premium, implemented_mitigation_measures
        )

        # Calculate potential premium with discounts
        potential_premium = self._calculate_potential_premium(
            total_premium, discount_opportunities
        )

        # Generate alerts
        alerts = self._generate_alerts(
            risk_components, climate_projections, zone_concentration
        )

        # Calculate next review date
        next_review = self._calculate_next_review_date(
            climate_projections.get("temperature_increase_2050", 1.8)
        )

        # Calculate standard premium (without risk adjustments)
        standard_premium = (
            expected_claims * 1.2
        )  # Basic 20% loading for standard premium

        # Format climate risk breakdown
        climate_breakdown = {
            "physical_risk": {
                "score": risk_components.physical_risk,
                "risk_type": "inundação",
                "projection_to_2050": f'→ {climate_projections.get("risk_increase_percentage", 129.0)}% até {climate_projections.get("year", 2050)}',
            },
            "transition_risk": {
                "score": risk_components.transition_risk,
                "details": f"CarbonTax R$ {risk_components.transition_risk*150:.0f}/ano",  # Simplified calculation
            },
            "mitigation_effect": {
                "points_reduction": -abs(
                    risk_components.mitigation_effect * 100
                ),  # Convert to points reduction
                "measures_detected": implemented_mitigation_measures or ["none"],
            },
        }

        return PolicyAnalysisReport(
            policy_id=policy_id,
            risk_level=risk_level,
            scr_score=risk_components.scr_score,
            climate_risk_breakdown=climate_breakdown,
            decision=decision,
            decision_reason=decision_reason,
            final_premium=total_premium,
            standard_premium=standard_premium,
            component_analysis={
                "expected_loss": premium_breakdown.expected_loss,
                "security_loading": premium_breakdown.security_loading,
                "security_loading_percentage": f'CS={self.component_weights["security_loading_rate"]*100:.0f}%',
                "contingency_loading": premium_breakdown.contingency_loading,
                "contingency_loading_percentage": f'CCC={self.component_weights["contingency_loading_rate"]*100:.0f}%',
                "margin_loading": premium_breakdown.margin_loading,
                "margin_loading_percentage": f'ML={self.component_weights["margin_loading_rate"]*100:.0f}%',
                "investment_return": premium_breakdown.investment_return,
                "investment_return_percentage": f'TR={self.component_weights["investment_return_rate"]*100:.0f}%',
                "climate_change_loading": premium_breakdown.climate_change_loading,
                "climate_change_percentage": f'CC={self.component_weights["climate_change_rate"]*100:.0f}%',
                "capacity_adjustment": premium_breakdown.capacity_adjustment,
                "capacity_adjustment_percentage": f"Capacidade={zone_concentration*100:.0f}%",
            },
            discount_opportunities=discount_opportunities,
            potential_premium=potential_premium,
            alerts=alerts,
            next_review_date=next_review,
            calculation_timestamp=datetime.now(),
        )

    def _get_risk_level(self, scr_score: float) -> str:
        """Determine risk level based on SCR score"""
        for level, (min_val, max_val) in self.risk_thresholds.items():
            if min_val <= scr_score < max_val:
                return level.upper()

        return "CRITICAL"  # Default for scores above critical threshold

    def _calculate_premium_breakdown(
        self, expected_claims: float, scr_score: float, zone_concentration: float
    ) -> PremiumBreakdown:
        """Calculate premium components breakdown"""
        # Base expected loss
        expected_loss = expected_claims

        # Calculate loadings based on component weights and risk level
        security_loading = (
            expected_loss * self.component_weights["security_loading_rate"]
        )
        contingency_loading = (
            expected_loss * self.component_weights["contingency_loading_rate"]
        )
        margin_loading = expected_loss * self.component_weights["margin_loading_rate"]
        investment_return = (
            expected_loss * self.component_weights["investment_return_rate"]
        )
        climate_change_loading = (
            expected_loss * self.component_weights["climate_change_rate"]
        )

        # Capacity adjustment based on zone concentration
        capacity_adjustment = (
            expected_loss
            * zone_concentration
            * self.component_weights["capacity_adjustment_rate"]
        )

        return PremiumBreakdown(
            expected_loss=expected_loss,
            security_loading=security_loading,
            contingency_loading=contingency_loading,
            margin_loading=margin_loading,
            investment_return=investment_return,
            climate_change_loading=climate_change_loading,
            capacity_adjustment=capacity_adjustment,
        )

    def _determine_policy_decision(
        self, scr_score: float, implemented_mitigation_measures: List[str]
    ) -> Tuple[str, str]:
        """Determine policy decision based on SCR score and mitigation measures"""
        if scr_score < self.decision_thresholds["approve"]:
            return "APROVADA", "Risco aceitável com mitigação adequada"
        elif scr_score < self.decision_thresholds["reject"]:
            # For scores in conditional range, check if specific mitigation is needed
            if (
                scr_score > self.decision_thresholds["condition"] - 50
            ):  # Close to rejection threshold
                if (
                    "pumping_system" not in implemented_mitigation_measures
                    and scr_score > 650
                ):
                    return "CONDICIONADA", "requer sistema de bombeamento"
                else:
                    return "APROVADA_COM_CONDICOES", "Aprovada com condições aplicáveis"
            else:
                return "CONDICIONADA", "requer melhorias de mitigação"
        else:
            return "REJEITADA", "Risco excessivamente alto mesmo com mitigação"

    def _generate_discount_opportunities(
        self, current_premium: float, implemented_measures: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate discount opportunities based on current premium and existing measures"""
        opportunities = []

        # Find measures that are not yet implemented
        for measure_key, details in self.discount_opportunities.items():
            measure_name = details["name"]
            if measure_name not in implemented_measures:
                opportunities.append(
                    {
                        "opportunity": measure_name,
                        "description": details["description"],
                        "discount_amount": details["discount_amount"],
                        "mitigation_type": details["mitigation_type"],
                        "implementation_cost": details["implementation_cost"],
                        "payback_period_months": details["payback_period_months"],
                    }
                )

        return opportunities

    def _calculate_potential_premium(
        self, current_premium: float, discount_opportunities: List[Dict[str, Any]]
    ) -> float:
        """Calculate potential premium with discount opportunities applied"""
        total_discount = sum(
            op["discount_amount"] for op in discount_opportunities[:2]
        )  # Apply top 2 discounts
        return max(0, current_premium - total_discount)

    def _generate_alerts(
        self,
        risk_components: ClimateRiskComponents,
        climate_projections: Dict[str, float],
        zone_concentration: float,
    ) -> List[str]:
        """Generate relevant alerts based on risk components"""
        alerts = []

        # Climate projection alert
        risk_increase = climate_projections.get("risk_increase_percentage", 129.0)
        year = climate_projections.get("year", 2050)
        alerts.append(
            f"Zona com projeção de aumento de sinistralidade {risk_increase}% até {year}"
        )

        # Revenue loss recommendation if concentration risk is high
        if risk_components.concentration_risk > 0.5:
            alerts.append("Recomenda-se cobertura complementar de perda de renda")

        # Reinsurance alert if physical risk is high
        if risk_components.physical_risk > 0.7 and zone_concentration > 0.20:
            alerts.append("Resseguro automático: 40% quota-share ativado")

        # Temperature threshold alert
        temp_proj = climate_projections.get("temperature_increase_2050", 1.8)
        if temp_proj > 1.5:
            alerts.append(
                f"Atenção: Projeção de aumento térmico acima de 1.5°C ({temp_proj}°C)"
            )

        # Mitigation alert if low mitigation effectiveness
        if risk_components.mitigation_effect < 0.1:
            alerts.append("Avaliar implementação de medidas de mitigação adequadas")

        return alerts

    def _calculate_next_review_date(self, temperature_projection: float) -> datetime:
        """Calculate next review date based on climate projections"""
        next_review = datetime.now() + relativedelta(months=12)

        # If temperature projection is high, suggest more frequent reviews
        if temperature_projection > 2.0:
            next_review = datetime.now() + relativedelta(
                months=6
            )  # 6-month review for high temp increase

        return next_review

    def generate_policy_comparison_report(
        self, policies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate comparison report for multiple policies"""
        reports = []
        total_premium = 0.0
        average_scr = 0.0
        risk_distribution = {
            "VERY_LOW": 0,
            "LOW": 0,
            "MODERATE": 0,
            "HIGH": 0,
            "CRITICAL": 0,
        }

        for policy_data in policies:
            # Create risk components from the policy data
            risk_components = ClimateRiskComponents(
                physical_risk=policy_data.get("physical_risk", 0.42),
                transition_risk=policy_data.get("transition_risk", 0.19),
                concentration_risk=policy_data.get("concentration_risk", 0.15),
                mitigation_effect=policy_data.get("mitigation_effect", 0.07),
                expected_claims=policy_data.get("expected_claims", 1050),
            )

            report = self.generate_policy_analysis_report(
                policy_id=policy_data.get("policy_id", "UNKNOWN"),
                risk_components=risk_components,
                expected_claims=policy_data.get("expected_claims", 1050),
                coverage_amount=policy_data.get("coverage_amount", 10000),
                zone_concentration=policy_data.get("zone_concentration", 0.22),
                climate_projections=policy_data.get(
                    "climate_projections",
                    {
                        "temperature_increase_2050": 1.8,
                        "risk_increase_percentage": 129.0,
                        "year": 2050,
                    },
                ),
                implemented_mitigation_measures=policy_data.get(
                    "implemented_mitigation_measures", []
                ),
                mitigation_impact=policy_data.get(
                    "mitigation_impact",
                    {"points_reduction": 70, "measures_list": ["drenagem", "sensores"]},
                ),
            )

            reports.append(report)
            total_premium += report.final_premium
            average_scr += report.scr_score
            risk_distribution[report.risk_level] += 1

        if len(reports) > 0:
            average_scr /= len(reports)

        return {
            "policy_count": len(reports),
            "total_portfolio_premium": total_premium,
            "average_scr_score": average_scr,
            "risk_distribution": risk_distribution,
            "individual_reports": [
                {
                    "policy_id": report.policy_id,
                    "risk_level": report.risk_level,
                    "scr_score": report.scr_score,
                    "final_premium": report.final_premium,
                    "decision": report.decision,
                    "decision_reason": report.decision_reason,
                }
                for report in reports
            ],
            "portfolio_summary": {
                "high_risk_policies": risk_distribution["HIGH"]
                + risk_distribution["CRITICAL"],
                "conditional_approvals": sum(
                    1 for r in reports if r.decision == "CONDICIONADA"
                ),
                "recommended_actions": self._aggregate_portfolio_recommendations(
                    reports
                ),
            },
            "generation_timestamp": datetime.now().isoformat(),
        }

    def _aggregate_portfolio_recommendations(
        self, reports: List[PolicyAnalysisReport]
    ) -> List[str]:
        """Aggregate recommendations across multiple policy reports"""
        recommendations = []

        high_risk_count = sum(
            1 for r in reports if r.risk_level in ["HIGH", "CRITICAL"]
        )
        conditional_count = sum(1 for r in reports if r.decision == "CONDICIONADA")

        if high_risk_count > len(reports) * 0.3:  # More than 30% high risk
            recommendations.append(
                "Avaliar restrição de aceitação para a região devido a alta concentração de risco"
            )

        if conditional_count > 0:
            recommendations.append(
                f"Implementar {conditional_count} políticas condicionadas com exigências de mitigação"
            )

        if len(reports) > 0:
            avg_zone_concentration = np.mean(
                [
                    (
                        r.component_analysis["capacity_adjustment"]
                        / r.component_analysis["expected_loss"]
                        * 100
                        if r.component_analysis["expected_loss"] > 0
                        else 0
                    )
                    for r in reports
                ]
            )
            if avg_zone_concentration > 25:
                recommendations.append(
                    f"Reduzir concentração geográfica (atual média {avg_zone_concentration:.1f}%)"
                )

        if not recommendations:
            recommendations.append("Portfólio com perfil de risco aceitável")

        return recommendations


# Global instance
climate_report_generator = ClimateRiskReportService()


def generate_policy_analysis_report(
    policy_id: str,
    risk_components: ClimateRiskComponents,
    expected_claims: float,
    coverage_amount: float,
    zone_concentration: float = 0.22,
    climate_projections: Optional[Dict[str, float]] = None,
    implemented_mitigation_measures: Optional[List[str]] = None,
    mitigation_impact: Optional[Dict[str, float]] = None,
) -> PolicyAnalysisReport:
    """Convenience function to generate policy analysis report"""
    return climate_report_generator.generate_policy_analysis_report(
        policy_id,
        risk_components,
        expected_claims,
        coverage_amount,
        zone_concentration,
        climate_projections,
        implemented_mitigation_measures,
        mitigation_impact,
    )


def generate_policy_comparison_report(policies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function to generate policy comparison report"""
    return climate_report_generator.generate_policy_comparison_report(policies)
