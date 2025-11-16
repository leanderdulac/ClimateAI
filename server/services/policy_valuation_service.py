"""
Policy Valuation and Notification Service
Identifies valuable policies and notifies administrators when policies are worth pursuing.
Also provides interactive options to improve policy valuation.
"""
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class PolicyValuationTier(Enum):
    """Classification for policy valuation tiers"""
    EXCELLENT = "excellent"  # High value, low risk
    GOOD = "good"            # Good value, moderate risk
    FAIR = "fair"            # Average value, acceptable risk
    POOR = "poor"            # Low value, high risk
    AVOID = "avoid"          # Should be avoided

@dataclass
class PolicyMetrics:
    """Current metrics for a policy"""
    premium_amount: float
    expected_claims: float
    claim_frequency: float
    claim_severity: float
    climate_risk_score: float  # 0-1000 scale
    physical_risk: float      # 0-1 scale
    transition_risk: float    # 0-1 scale
    mitigation_effectiveness: float  # 0-1 scale (higher is better)
    model_confidence: float   # 0-1 scale
    concentration_risk: float # 0-1 scale
    geographic_factor: float  # 0-1 scale
    regulatory_factor: float  # 0-1 scale
    economic_factor: float    # 0-1 scale

@dataclass
class PolicyValuation:
    """Valuation result for a policy"""
    policy_id: str
    valuation_tier: PolicyValuationTier
    valuation_score: float  # 0-100 scale
    profitability_score: float  # 0-100 scale
    risk_reward_ratio: float
    premium_efficiency: float
    improvement_potential: float  # How much improvement is possible
    current_metrics: PolicyMetrics
    recommended_actions: List[str]
    notification_required: bool
    notification_priority: int  # 1-5, 5 being highest priority
    calculation_timestamp: datetime

@dataclass
class ImprovementOption:
    """Option for improving policy valuation"""
    option_id: str
    option_name: str
    description: str
    cost: float  # Cost to implement
    expected_benefit: float  # Expected benefit in premium efficiency
    risk_reduction: float  # Risk reduction factor (0-1)
    implementation_time_days: int
    success_probability: float  # Probability of successful implementation
    category: str  # mitigation, pricing, coverage, etc.

@dataclass
class InteractivePolicyAnalysis:
    """Results of interactive policy analysis"""
    policy_id: str
    current_valuation: PolicyValuation
    improvement_options: List[ImprovementOption]
    top_recommendations: List[ImprovementOption]
    estimated_roi: float
    implementation_timeline: str
    confidence_level: float
    analysis_timestamp: datetime

class PolicyValuationService:
    """
    Service for policy valuation, notification, and improvement recommendations
    Implements sophisticated analysis to identify valuable policies and actionable improvements
    """
    
    def __init__(self):
        # Valuation thresholds
        self.valuation_thresholds = {
            'excellent_min': 80,
            'good_min': 65,
            'fair_min': 50,
            'poor_min': 30
        }
        
        # Notification thresholds
        self.notification_thresholds = {
            'excellent': True,  # Always notify for excellent policies
            'good_high_confidence': 0.8,  # Notify for good policies with high confidence
            'fair_high_risk_reduction': 0.15  # Notify if good improvement potential
        }
        
        self.risk_weights = {
            'climate_risk': 0.25,
            'physical_risk': 0.20,
            'transition_risk': 0.15,
            'concentration_risk': 0.10,
            'model_uncertainty': 0.10
        }
        
        # Improvement option templates
        self.improvement_templates = [
            {
                'id': 'MITIGATION_UPGRADE',
                'name': 'Mitigation Measures Upgrade',
                'description': 'Implement or upgrade mitigation measures to reduce climate risk',
                'cost_factor': 0.02,  # 2% of policy value
                'benefit_factor': 0.15,  # 15% improvement in premium efficiency
                'risk_reduction_factor': 0.30,
                'time_days': 45,
                'success_probability': 0.85,
                'category': 'mitigation'
            },
            {
                'id': 'PARAMETRIC_ADJUSTMENT',
                'name': 'Parametric Coverage Adjustment',
                'description': 'Adjust parametric triggers for better risk coverage balance',
                'cost_factor': 0.005,  # 0.5% of policy value
                'benefit_factor': 0.10,
                'risk_reduction_factor': 0.15,
                'time_days': 15,
                'success_probability': 0.90,
                'category': 'coverage'
            },
            {
                'id': 'ZONE_DIVERSIFICATION',
                'name': 'Geographic Diversification',
                'description': 'Diversify risk across different geographic zones',
                'cost_factor': 0.01,  # 1% of policy value
                'benefit_factor': 0.08,
                'risk_reduction_factor': 0.25,
                'time_days': 30,
                'success_probability': 0.75,
                'category': 'concentration'
            },
            {
                'id': 'DATA_ENHANCEMENT',
                'name': 'Data Enhancement',
                'description': 'Improve data quality and monitoring systems',
                'cost_factor': 0.008,  # 0.8% of policy value
                'benefit_factor': 0.12,
                'risk_reduction_factor': 0.05,
                'time_days': 20,
                'success_probability': 0.95,
                'category': 'data'
            },
            {
                'id': 'COVERAGE_OPTIMIZATION',
                'name': 'Coverage Optimization',
                'description': 'Optimize coverage limits and deductibles',
                'cost_factor': 0.002,  # 0.2% of policy value
                'benefit_factor': 0.05,
                'risk_reduction_factor': 0.10,
                'time_days': 10,
                'success_probability': 0.80,
                'category': 'pricing'
            }
        ]
        
        # Store notifications
        self.notifications_queue: List[Dict] = []
        self.processed_policies: Dict[str, PolicyValuation] = {}

    def calculate_policy_valuation(self, 
                                 policy_id: str,
                                 metrics: PolicyMetrics,
                                 policy_value: Optional[float] = None) -> PolicyValuation:
        """
        Calculate comprehensive policy valuation based on multiple factors
        
        Args:
            policy_id: Policy identifier
            metrics: Policy metrics including risk factors
            policy_value: Total policy value (if known)
            
        Returns:
            PolicyValuation with complete analysis
        """
        try:
            # Calculate profitability score (1 - expected_claims/premium, capped)
            if metrics.premium_amount > 0:
                profitability = max(0, min(1, 1 - (metrics.expected_claims / metrics.premium_amount)))
                profitability_score = profitability * 100
            else:
                profitability_score = 50  # neutral if no premium information

            # Calculate risk score (lower is better)
            risk_components = [
                metrics.climate_risk_score / 1000,  # Normalize to 0-1
                metrics.physical_risk,
                metrics.transition_risk,
                metrics.concentration_risk,
                (1 - metrics.mitigation_effectiveness),  # Inverse - less mitigation = more risk
                (1 - metrics.model_confidence)  # Less confidence = more risk
            ]
            
            # Weighted risk score (higher = more risky)
            weighted_risk = sum(comp * weight for comp, weight in 
                              zip(risk_components, self.risk_weights.values()))
            
            # Calculate premium efficiency (how well premium covers expected losses adjusted for risk)
            if metrics.expected_claims > 0:
                base_efficiency = metrics.premium_amount / metrics.expected_claims
                # Adjust for risk factors
                risk_adjustment = (1 + weighted_risk) * (1 - metrics.mitigation_effectiveness * 0.3)
                premium_efficiency = base_efficiency / risk_adjustment
            else:
                premium_efficiency = 1.0  # neutral if no expected claims

            # Calculate risk-reward ratio (lower values indicate better risk-reward)
            risk_reward_ratio = weighted_risk / (profitability_score / 100) if profitability_score > 0 else 10.0

            # Overall valuation score combining multiple factors
            valuation_score = (
                profitability_score * 0.3 +
                (100 - weighted_risk * 100) * 0.3 +  # Lower risk = higher score
                premium_efficiency * 20 * 0.2 +  # Scale efficiency to 0-100 range
                metrics.model_confidence * 100 * 0.2  # Higher confidence = higher score
            )

            # Determine valuation tier based on score ranges
            if valuation_score >= 80:
                tier = PolicyValuationTier.EXCELLENT
                notification_needed = True
                priority = 5
            elif valuation_score >= 65:
                tier = PolicyValuationTier.GOOD
                notification_needed = True if metrics.model_confidence >= 0.7 else False
                priority = 4
            elif valuation_score >= 50:
                tier = PolicyValuationTier.FAIR
                notification_needed = False  # Only if improvement potential
                priority = 3
            else:
                tier = PolicyValuationTier.POOR
                notification_needed = False
                priority = 2

            # Calculate improvement potential based on mitigation effectiveness
            improvement_potential = (1 - metrics.mitigation_effectiveness) * 50  # Up to 50 points improvement possible

            # Generate recommended actions based on weaknesses
            recommendations = self._generate_recommendations(metrics, tier)

            # Determine if notification is required based on additional criteria
            if tier in [PolicyValuationTier.FAIR, PolicyValuationTier.POOR]:
                # If there's significant improvement potential, notify
                if improvement_potential > 20:  # More than 20% improvement possible
                    notification_needed = True
                    priority = max(priority, 3)

            valuation = PolicyValuation(
                policy_id=policy_id,
                valuation_tier=tier,
                valuation_score=valuation_score,
                profitability_score=profitability_score,
                risk_reward_ratio=risk_reward_ratio,
                premium_efficiency=premium_efficiency,
                improvement_potential=improvement_potential,
                current_metrics=metrics,
                recommended_actions=recommendations,
                notification_required=notification_needed,
                notification_priority=priority,
                calculation_timestamp=datetime.now()
            )

            # Store for future reference
            self.processed_policies[policy_id] = valuation

            # Queue notification if needed
            if notification_needed:
                self._queue_notification(valuation)

            return valuation

        except Exception as e:
            logger.error(f"Error calculating policy valuation for {policy_id}: {str(e)}")
            # Return a default valuation in case of error
            return PolicyValuation(
                policy_id=policy_id,
                valuation_tier=PolicyValuationTier.FAIR,
                valuation_score=50.0,
                profitability_score=50.0,
                risk_reward_ratio=1.0,
                premium_efficiency=1.0,
                improvement_potential=0.0,
                current_metrics=metrics,
                recommended_actions=["Erro no cálculo de avaliação"],
                notification_required=False,
                notification_priority=3,
                calculation_timestamp=datetime.now()
            )

    def _generate_recommendations(self, metrics: PolicyMetrics, tier: PolicyValuationTier) -> List[str]:
        """Generate tailored recommendations based on policy metrics and tier"""
        recommendations = []

        # Based on risk factors
        if metrics.climate_risk_score > 700:
            recommendations.append("Reduzir risco climático com mitigação especializada")
        if metrics.physical_risk > 0.6:
            recommendations.append("Implementar medidas de mitigação física")
        if metrics.transition_risk > 0.5:
            recommendations.append("Avaliar exposição a riscos de transição")
        if metrics.concentration_risk > 0.4:
            recommendations.append("Diversificar concentração geográfica")
        if metrics.mitigation_effectiveness < 0.4:
            recommendations.append("Melhorar medidas de mitigação existentes")
        if metrics.model_confidence < 0.6:
            recommendations.append("Melhorar qualidade dos dados e modelos")

        # Based on tier
        if tier in [PolicyValuationTier.POOR, PolicyValuationTier.AVOID]:
            recommendations.append("Considerar recusa ou reestruturação completa")
        elif tier == PolicyValuationTier.FAIR:
            recommendations.append("Avaliar cuidadosamente com mitigação adicional")
        elif tier == PolicyValuationTier.GOOD:
            recommendations.append("Boa oportunidade com devida diligência")
        elif tier == PolicyValuationTier.EXCELLENT:
            recommendations.append("Excelente oportunidade - priorizar subscrição")

        # Premium-related
        if metrics.premium_amount < metrics.expected_claims * 1.1:  # Premium too low
            recommendations.append("Ajustar prêmio para refletir melhor o risco esperado")
        elif metrics.premium_amount > metrics.expected_claims * 3:  # Premium too high
            recommendations.append("Considerar redução de carregamentos para competitividade")

        return recommendations

    def _queue_notification(self, valuation: PolicyValuation):
        """Queue notification for administrator"""
        notification = {
            'notification_id': f"NOTIF_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{valuation.policy_id}",
            'policy_id': valuation.policy_id,
            'valuation_tier': valuation.valuation_tier.value,
            'valuation_score': valuation.valuation_score,
            'priority': valuation.notification_priority,
            'timestamp': valuation.calculation_timestamp,
            'message': self._generate_notification_message(valuation),
            'recommended_actions': valuation.recommended_actions,
            'processed': False
        }
        self.notifications_queue.append(notification)
        logger.info(f"Notification queued for policy {valuation.policy_id} with tier {valuation.valuation_tier.value}")

    def _generate_notification_message(self, valuation: PolicyValuation) -> str:
        """Generate appropriate notification message based on valuation"""
        if valuation.valuation_tier == PolicyValuationTier.EXCELLENT:
            return f"🚨 POLÍCIA EXCEPCIONAL IDENTIFICADA: {valuation.policy_id} - Valorização de {valuation.valuation_score:.1f}/100"
        elif valuation.valuation_tier == PolicyValuationTier.GOOD:
            return f"✅ BOA OPORTUNIDADE: {valuation.policy_id} - Valorização de {valuation.valuation_score:.1f}/100"
        elif valuation.valuation_tier == PolicyValuationTier.FAIR and valuation.improvement_potential > 20:
            return f"💡 POTENCIAL DE MELHORIA: {valuation.policy_id} - Melhoria potencial de {valuation.improvement_potential:.1f} pts"
        else:
            return f"📊 POLÍCIA ANALISADA: {valuation.policy_id} - Valorização de {valuation.valuation_score:.1f}/100"

    def get_pending_notifications(self) -> List[Dict[str, Any]]:
        """Get all pending notifications"""
        return [notif for notif in self.notifications_queue if not notif['processed']]

    def mark_notification_as_processed(self, notification_id: str):
        """Mark a notification as processed"""
        for notif in self.notifications_queue:
            if notif['notification_id'] == notification_id:
                notif['processed'] = True
                break

    def get_interactive_policy_analysis(self,
                                      policy_id: str,
                                      metrics: PolicyMetrics,
                                      policy_value: Optional[float] = None,
                                      max_options: int = 5) -> InteractivePolicyAnalysis:
        """
        Generate interactive analysis with improvement options
        
        Args:
            policy_id: Policy identifier
            metrics: Current policy metrics
            policy_value: Total policy value (optional)
            max_options: Maximum number of improvement options to return
            
        Returns:
            InteractivePolicyAnalysis with options and recommendations
        """
        try:
            # First, calculate current valuation
            current_valuation = self.calculate_policy_valuation(policy_id, metrics, policy_value)

            # Generate improvement options based on current weaknesses
            options = self._generate_improvement_options(policy_id, metrics, policy_value)

            # Sort options by ROI potential (benefit/cost ratio)
            options_sorted = sorted(options, 
                                  key=lambda x: (x.expected_benefit / (x.cost if x.cost > 0 else 1)), 
                                  reverse=True)

            # Get top recommendations (best ROI)
            top_recommendations = options_sorted[:max_options]

            # Calculate estimated ROI from implementing top options
            total_cost = sum(opt.cost for opt in top_recommendations)
            total_benefit = sum(opt.expected_benefit for opt in top_recommendations)
            estimated_roi = (total_benefit / total_cost * 100) if total_cost > 0 else 0

            analysis = InteractivePolicyAnalysis(
                policy_id=policy_id,
                current_valuation=current_valuation,
                improvement_options=options,
                top_recommendations=top_recommendations,
                estimated_roi=estimated_roi,
                implementation_timeline=self._calculate_timeline(top_recommendations),
                confidence_level=np.mean([opt.success_probability for opt in top_recommendations]) if top_recommendations else 0.0,
                analysis_timestamp=datetime.now()
            )

            return analysis

        except Exception as e:
            logger.error(f"Error generating interactive analysis for {policy_id}: {str(e)}")
            # Return basic analysis on error
            current_valuation = self.calculate_policy_valuation(policy_id, metrics, policy_value)
            return InteractivePolicyAnalysis(
                policy_id=policy_id,
                current_valuation=current_valuation,
                improvement_options=[],
                top_recommendations=[],
                estimated_roi=0.0,
                implementation_timeline="N/A",
                confidence_level=0.0,
                analysis_timestamp=datetime.now()
            )

    def _generate_improvement_options(self, 
                                    policy_id: str, 
                                    metrics: PolicyMetrics, 
                                    policy_value: Optional[float] = None) -> List[ImprovementOption]:
        """Generate improvement options based on current policy metrics"""
        options = []
        base_value = policy_value or metrics.premium_amount

        for template in self.improvement_templates:
            # Calculate specific costs and benefits based on policy value
            cost = base_value * template['cost_factor'] if policy_value else 1000.0
            benefit = base_value * template['benefit_factor'] if policy_value else 1000.0

            # Adjust risk reduction based on current risk levels
            risk_reduction = template['risk_reduction_factor']
            
            # Adjust benefit based on current weaknesses
            if template['id'] == 'MITIGATION_UPGRADE' and metrics.mitigation_effectiveness < 0.5:
                benefit *= 1.5  # Higher benefit for weak mitigation
                risk_reduction *= 1.5
            elif template['id'] == 'ZONE_DIVERSIFICATION' and metrics.concentration_risk > 0.5:
                benefit *= 1.3  # Higher benefit for high concentration risk
            elif template['id'] == 'PARAMETRIC_ADJUSTMENT' and metrics.model_confidence < 0.6:
                benefit *= 1.2  # Higher benefit for low model confidence

            option = ImprovementOption(
                option_id=template['id'],
                option_name=template['name'],
                description=template['description'],
                cost=cost,
                expected_benefit=benefit,
                risk_reduction=risk_reduction,
                implementation_time_days=template['time_days'],
                success_probability=template['success_probability'],
                category=template['category']
            )
            options.append(option)

        return options

    def _calculate_timeline(self, recommendations: List[ImprovementOption]) -> str:
        """Calculate implementation timeline based on recommendations"""
        if not recommendations:
            return "N/A"
        
        # Timeline based on the longest implementation time among recommendations
        max_time = max((opt.implementation_time_days for opt in recommendations), default=0)
        
        if max_time <= 10:
            return "1-2 semanas"
        elif max_time <= 30:
            return "1 mês"
        elif max_time <= 60:
            return "2 meses"
        elif max_time <= 90:
            return "3 meses"
        else:
            return f"{max_time // 30}+ meses"

    def get_policy_recommendations_summary(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of recommendations for a specific policy"""
        if policy_id not in self.processed_policies:
            return None

        valuation = self.processed_policies[policy_id]
        
        return {
            'policy_id': policy_id,
            'current_valuation': {
                'tier': valuation.valuation_tier.value,
                'score': valuation.valuation_score,
                'profitability': valuation.profitability_score,
                'premium_efficiency': valuation.premium_efficiency
            },
            'key_weaknesses': self._identify_weaknesses(valuation.current_metrics),
            'improvement_potential': valuation.improvement_potential,
            'recommended_actions': valuation.recommended_actions,
            'notification_required': valuation.notification_required,
            'last_analysis': valuation.calculation_timestamp.isoformat()
        }

    def _identify_weaknesses(self, metrics: PolicyMetrics) -> List[str]:
        """Identify key weaknesses in policy metrics"""
        weaknesses = []
        
        if metrics.climate_risk_score > 600:
            weaknesses.append(f"Alto risco climático: {metrics.climate_risk_score}/1000")
        if metrics.physical_risk > 0.5:
            weaknesses.append(f"Alto risco físico: {metrics.physical_risk:.2f}")
        if metrics.transition_risk > 0.4:
            weaknesses.append(f"Alto risco de transição: {metrics.transition_risk:.2f}")
        if metrics.mitigation_effectiveness < 0.5:
            weaknesses.append(f"Baixa efetividade de mitigação: {metrics.mitigation_effectiveness:.2f}")
        if metrics.model_confidence < 0.6:
            weaknesses.append(f"Baixa confiança do modelo: {metrics.model_confidence:.2f}")
        if metrics.concentration_risk > 0.3:
            weaknesses.append(f"Alto risco de concentração: {metrics.concentration_risk:.2f}")

        return weaknesses

    def get_valuable_policies_summary(self, min_score: float = 70) -> List[Dict[str, Any]]:
        """Get summary of policies with valuation above threshold"""
        valuable_policies = []
        
        for policy_id, valuation in self.processed_policies.items():
            if valuation.valuation_score >= min_score:
                valuable_policies.append({
                    'policy_id': policy_id,
                    'valuation_score': valuation.valuation_score,
                    'valuation_tier': valuation.valuation_tier.value,
                    'profitability_score': valuation.profitability_score,
                    'premium_efficiency': valuation.premium_efficiency,
                    'risk_reward_ratio': valuation.risk_reward_ratio,
                    'last_analysis': valuation.calculation_timestamp.isoformat()
                })
        
        # Sort by valuation score descending
        valuable_policies.sort(key=lambda x: x['valuation_score'], reverse=True)
        return valuable_policies

# Global instance
policy_valuation_service = PolicyValuationService()

def calculate_policy_valuation(policy_id: str, metrics: PolicyMetrics, policy_value: Optional[float] = None) -> PolicyValuation:
    """Convenience function to calculate policy valuation"""
    return policy_valuation_service.calculate_policy_valuation(policy_id, metrics, policy_value)

def get_interactive_policy_analysis(
    policy_id: str,
    metrics: PolicyMetrics,
    policy_value: Optional[float] = None,
    max_options: int = 5
) -> InteractivePolicyAnalysis:
    """Convenience function to get interactive policy analysis"""
    return policy_valuation_service.get_interactive_policy_analysis(policy_id, metrics, policy_value, max_options)

def get_pending_notifications() -> List[Dict[str, Any]]:
    """Convenience function to get pending notifications"""
    return policy_valuation_service.get_pending_notifications()

def get_policy_recommendations_summary(policy_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get policy recommendations summary"""
    return policy_valuation_service.get_policy_recommendations_summary(policy_id)

def get_valuable_policies_summary(min_score: float = 70) -> List[Dict[str, Any]]:
    """Convenience function to get valuable policies summary"""
    return policy_valuation_service.get_valuable_policies_summary(min_score)

def mark_notification_as_processed(notification_id: str):
    """Convenience function to mark notification as processed"""
    policy_valuation_service.mark_notification_as_processed(notification_id)