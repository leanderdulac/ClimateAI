"""
Dynamic Insurance Pricing and Profitability Analysis Service
Implements advanced dynamic evaluation system with profitability tracking and portfolio optimization.
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from collections import defaultdict
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class PolicyPerformance:
    """Policy-level performance metrics"""
    policy_id: str
    premium: float
    expected_claims: float
    actual_claims: float
    profit_margin: float
    risk_score: float
    profitability_score: float
    coverage_amount: float
    duration_months: int
    portfolio_contribution: float

@dataclass
class PortfolioMetrics:
    """Portfolio-level performance metrics"""
    total_premium: float
    total_expected_claims: float
    total_actual_claims: float
    total_profit: float
    profitability_ratio: float
    combined_ratio: float
    portfolio_size: int
    risk_weighted_premium: float
    return_on_risk: float

@dataclass
class DynamicPricingAdjustment:
    """Adjustment parameters for dynamic pricing"""
    base_rate_multiplier: float
    risk_adjustment: float
    market_condition_adjustment: float
    portfolio_balance_adjustment: float
    competitive_positioning: float

class DynamicInsuranceAnalysisService:
    """
    Advanced service for dynamic insurance pricing and profitability analysis
    Implements: Dynamic pricing = Base_rate * (1 + risk_adjustment) * market_multiplier
    with profitability optimization and portfolio risk management
    """

    def __init__(self):
        self.policies_db = {}  # Store policy data
        self.portfolio_performance = defaultdict(list)
        self.competitor_pricing = {}  # Track competitor rates
        self.market_conditions = {}  # Track market factors
        self.scaler = StandardScaler()
        self.pricing_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model_trained = False
        self.profitability_threshold = 0.05  # Minimum 5% profit margin
        self.claims_history = []
        
        # Initialize market condition factors
        self._initialize_market_conditions()

    def _initialize_market_conditions(self):
        """Initialize baseline market condition factors"""
        self.market_conditions = {
            'interest_rate': 0.08,  # 8% base rate
            'inflation_rate': 0.05,  # 5% inflation
            'economic_growth': 0.02,  # 2% growth
            'regulatory_factor': 1.0,  # Neutral initially
            'competition_intensity': 0.7,  # 0-1 scale (1 = very competitive)
            'climate_risk_premium': 0.03  # 3% additional for climate risk
        }

    def add_policy_data(self, policy_id: str, premium: float, expected_claims: float,
                       coverage_amount: float, risk_factors: Dict[str, float],
                       duration_months: int = 12, actual_claims: float = 0.0) -> None:
        """
        Add policy data for analysis and learning
        
        Args:
            policy_id: Unique identifier for the policy
            premium: Premium amount charged
            expected_claims: Anticipated claims amount
            coverage_amount: Total coverage amount
            risk_factors: Dictionary of risk factors
            duration_months: Duration of the policy in months
            actual_claims: Actual claims paid (0 if not yet known)
        """
        self.policies_db[policy_id] = {
            'premium': premium,
            'expected_claims': expected_claims,
            'coverage_amount': coverage_amount,
            'risk_factors': risk_factors,
            'duration_months': duration_months,
            'actual_claims': actual_claims,
            'profit': premium - expected_claims,
            'profit_margin': (premium - expected_claims) / premium if premium > 0 else 0,
            'timestamp': datetime.now().isoformat()
        }

    def calculate_portfolio_metrics(self) -> PortfolioMetrics:
        """
        Calculate comprehensive portfolio metrics
        
        Returns:
            PortfolioMetrics object with key performance indicators
        """
        if not self.policies_db:
            return PortfolioMetrics(
                total_premium=0, total_expected_claims=0, total_actual_claims=0,
                total_profit=0, profitability_ratio=0, combined_ratio=0,
                portfolio_size=0, risk_weighted_premium=0, return_on_risk=0
            )

        total_premium = sum(p['premium'] for p in self.policies_db.values())
        total_expected_claims = sum(p['expected_claims'] for p in self.policies_db.values())
        total_actual_claims = sum(p['actual_claims'] for p in self.policies_db.values())
        total_profit = total_premium - total_actual_claims
        portfolio_size = len(self.policies_db)
        
        # Calculate profitability ratio
        profitability_ratio = (total_profit / total_premium) if total_premium > 0 else 0
        
        # Combined ratio (claims + expenses / premium)
        combined_ratio = (total_actual_claims / total_premium) if total_premium > 0 else 0
        
        # Risk-weighted premium based on average risk factors
        avg_risk_factor = np.mean([
            np.mean(list(p['risk_factors'].values())) if p['risk_factors'] else 0
            for p in self.policies_db.values()
        ]) if self.policies_db else 0
        
        risk_weighted_premium = total_premium * (1 + avg_risk_factor)
        return_on_risk = total_profit / (total_expected_claims + 1)  # +1 to avoid division by zero

        return PortfolioMetrics(
            total_premium=total_premium,
            total_expected_claims=total_expected_claims,
            total_actual_claims=total_actual_claims,
            total_profit=total_profit,
            profitability_ratio=profitability_ratio,
            combined_ratio=combined_ratio,
            portfolio_size=portfolio_size,
            risk_weighted_premium=risk_weighted_premium,
            return_on_risk=return_on_risk
        )

    def calculate_policy_profitability_score(self, policy_id: str) -> float:
        """
        Calculate profitability score for a specific policy (0-1 scale, 1 being highly profitable)
        
        Args:
            policy_id: ID of the policy to evaluate
            
        Returns:
            Profitability score (0-1)
        """
        if policy_id not in self.policies_db:
            return 0.0

        policy = self.policies_db[policy_id]
        profit_margin = policy['profit_margin']
        
        # Map profit margin to 0-1 scale (positive margins scale up to 1, negative to 0)
        # Using a sigmoid-like transformation
        if profit_margin >= 0.2:  # Highly profitable
            return 1.0
        elif profit_margin >= 0:  # Marginally profitable
            return 0.5 + (profit_margin / 0.4)  # Normalize 0-0.2 to 0.5-1.0
        else:  # Unprofitable
            return max(0.0, 0.1 + (profit_margin / 0.5))  # Normalize negative margins

    def calculate_pricing_adjustments(self, risk_factors: Dict[str, float]) -> DynamicPricingAdjustment:
        """
        Calculate dynamic pricing adjustments based on current conditions
        
        Args:
            risk_factors: Current risk factors for the policy
            
        Returns:
            DynamicPricingAdjustment with adjustment parameters
        """
        portfolio_metrics = self.calculate_portfolio_metrics()
        
        # Base rate multiplier based on portfolio performance
        if portfolio_metrics.profitability_ratio < 0.05:
            # Underperforming portfolio needs higher rates
            base_rate_multiplier = 1.2
        elif portfolio_metrics.profitability_ratio > 0.15:
            # Overperforming portfolio can afford competitive rates
            base_rate_multiplier = 0.9
        else:
            # Neutral performance
            base_rate_multiplier = 1.0

        # Risk adjustment based on risk factors
        risk_sum = sum(risk_factors.values()) if risk_factors else 0
        risk_adjustment = max(0.05, min(0.5, risk_sum * 0.2))  # 5-50% adjustment

        # Market condition adjustment
        market_factor = (
            (1 + self.market_conditions['inflation_rate']) *
            (1 + self.market_conditions['climate_risk_premium']) *
            (1 + self.market_conditions['competition_intensity'] * 0.05)
        )

        # Portfolio balance adjustment
        # If portfolio is too heavily weighted in high-risk areas
        if portfolio_metrics.combined_ratio > 0.9:
            portfolio_balance_adjustment = 1.15  # Increase rates to improve margins
        elif portfolio_metrics.combined_ratio < 0.7:
            portfolio_balance_adjustment = 0.95  # Can be more competitive
        else:
            portfolio_balance_adjustment = 1.0

        # Competitive positioning based on market data
        avg_premium = portfolio_metrics.total_premium / portfolio_metrics.portfolio_size if portfolio_metrics.portfolio_size > 0 else 0
        target_premium = self._calculate_target_premium(risk_factors)
        competitive_positioning = target_premium / avg_premium if avg_premium > 0 else 1.0

        return DynamicPricingAdjustment(
            base_rate_multiplier=base_rate_multiplier,
            risk_adjustment=risk_adjustment,
            market_condition_adjustment=market_factor,
            portfolio_balance_adjustment=portfolio_balance_adjustment,
            competitive_positioning=competitive_positioning
        )

    def _calculate_target_premium(self, risk_factors: Dict[str, float]) -> float:
        """
        Calculate target premium based on risk factors and market conditions
        """
        # Base premium as percentage of expected claims to ensure profitability
        base_premium = 1000  # Base premium for minimal risk

        # Weight different risk factors
        risk_multiplier = 1.0
        for factor_name, factor_value in risk_factors.items():
            if 'climate' in factor_name.lower() or 'temperature' in factor_name.lower():
                risk_multiplier *= (1 + factor_value * 0.8)  # Climate risks weighted more
            elif 'precipitation' in factor_name.lower() or 'flood' in factor_name.lower():
                risk_multiplier *= (1 + factor_value * 0.7)
            elif 'wind' in factor_name.lower():
                risk_multiplier *= (1 + factor_value * 0.5)
            else:
                risk_multiplier *= (1 + factor_value * 0.3)  # Default weight

        # Apply market conditions
        market_multiplier = (
            1 + self.market_conditions['inflation_rate'] +
            self.market_conditions['climate_risk_premium']
        )

        return base_premium * risk_multiplier * market_multiplier

    def calculate_dynamic_premium(self, coverage_amount: float,
                                risk_factors: Dict[str, float],
                                base_loading_factor: float = 0.20) -> Dict[str, Any]:
        """
        Calculate dynamic premium with comprehensive profitability analysis

        Args:
            coverage_amount: Amount of coverage requested
            risk_factors: Risk factors for the policy
            base_loading_factor: Base loading factor (default 20%)

        Returns:
            Dictionary with premium calculation and analysis
        """
        # Calculate expected claims based on risk factors
        expected_claims = self._estimate_expected_claims(coverage_amount, risk_factors)

        # Calculate target premium as expected claims + loadings to ensure profitability
        # Ensure minimum profitability threshold
        required_profit = expected_claims * self.profitability_threshold
        base_premium = expected_claims + required_profit  # Base for profitability

        # Apply risk loading factor
        risk_sum = sum(risk_factors.values()) if risk_factors else 0
        risk_loading = max(0.05, min(0.50, risk_sum * 0.3))  # 5-50% risk loading
        risk_based_premium = base_premium * (1 + risk_loading)

        # Apply market condition adjustment
        market_factor = (
            1 + self.market_conditions['inflation_rate'] +
            self.market_conditions['climate_risk_premium']
        )
        market_adjusted_premium = risk_based_premium * market_factor

        # Apply portfolio balance adjustment
        portfolio_metrics = self.calculate_portfolio_metrics()
        if portfolio_metrics.profitability_ratio < 0.05:
            portfolio_balance_adjustment = 1.15  # Increase rates by 15% if portfolio underperforming
        elif portfolio_metrics.profitability_ratio > 0.15:
            portfolio_balance_adjustment = 0.95  # Decrease rates by 5% if overperforming
        else:
            portfolio_balance_adjustment = 1.0
        final_premium = market_adjusted_premium * portfolio_balance_adjustment

        # Calculate profitability metrics
        profit = final_premium - expected_claims
        profit_margin = profit / final_premium if final_premium > 0 else 0

        # Calculate adjustments info for the return
        adjustments = {
            'base_rate_multiplier': 1.0,
            'risk_adjustment': risk_loading,
            'market_condition_adjustment': market_factor,
            'portfolio_balance_adjustment': portfolio_balance_adjustment,
            'competitive_positioning': 1.0
        }

        return {
            'coverage_amount': coverage_amount,
            'final_premium': final_premium,
            'target_premium': base_premium,
            'expected_claims': expected_claims,
            'profit': profit,
            'profit_margin': profit_margin,
            'break_even_premium': expected_claims,
            'risk_loading': risk_loading,
            'loading_factor': final_premium / coverage_amount if coverage_amount > 0 else 0,
            'adjustments': adjustments,
            'risk_factors': risk_factors,
            'is_profitable': profit_margin >= self.profitability_threshold
        }

    def _estimate_expected_claims(self, coverage_amount: float, risk_factors: Dict[str, float]) -> float:
        """
        Estimate expected claims based on risk factors and historical data
        """
        if not risk_factors:
            # Default to 40% of coverage for minimal risk
            return coverage_amount * 0.40

        # Calculate risk score from factors
        risk_score = sum(risk_factors.values()) / len(risk_factors) if risk_factors else 0

        # Base claim ratio (40% for low risk, up to 80% for high risk)
        base_claim_ratio = 0.40 + (risk_score * 0.40)  # 40-80%

        # Avoid claims exceeding coverage amount
        return min(coverage_amount * base_claim_ratio, coverage_amount * 0.95)  # Max 95% of coverage

    def analyze_policy_profitability(self, policy_id: str) -> PolicyPerformance:
        """
        Analyze profitability of a specific policy
        
        Args:
            policy_id: ID of policy to analyze
            
        Returns:
            PolicyPerformance object with detailed analysis
        """
        if policy_id not in self.policies_db:
            raise ValueError(f"Policy {policy_id} not found in database")

        policy = self.policies_db[policy_id]
        
        # Calculate profitability metrics
        premium = policy['premium']
        expected_claims = policy['expected_claims']
        actual_claims = policy['actual_claims']
        coverage_amount = policy['coverage_amount']
        duration_months = policy['duration_months']
        
        # Profit calculations
        profit = premium - actual_claims
        expected_profit = premium - expected_claims
        profit_margin = profit / premium if premium > 0 else 0
        expected_profit_margin = expected_profit / premium if premium > 0 else 0
        
        # Risk score (from policy data)
        risk_score = np.mean(list(policy['risk_factors'].values())) if policy['risk_factors'] else 0.0
        
        # Profitability score (0-1 scale)
        profitability_score = self.calculate_policy_profitability_score(policy_id)
        
        # Portfolio contribution
        portfolio_metrics = self.calculate_portfolio_metrics()
        portfolio_contribution = (premium / portfolio_metrics.total_premium) if portfolio_metrics.total_premium > 0 else 0
        
        return PolicyPerformance(
            policy_id=policy_id,
            premium=premium,
            expected_claims=expected_claims,
            actual_claims=actual_claims,
            profit_margin=profit_margin,
            risk_score=risk_score,
            profitability_score=profitability_score,
            coverage_amount=coverage_amount,
            duration_months=duration_months,
            portfolio_contribution=portfolio_contribution
        )

    def get_profitability_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive profitability report
        
        Returns:
            Dictionary with portfolio and policy level analysis
        """
        portfolio_metrics = self.calculate_portfolio_metrics()
        
        # Analyze individual policies
        policy_analyses = {}
        profitable_policies = 0
        total_policies = len(self.policies_db)
        
        for policy_id in self.policies_db:
            try:
                analysis = self.analyze_policy_profitability(policy_id)
                policy_analyses[policy_id] = {
                    'premium': analysis.premium,
                    'expected_claims': analysis.expected_claims,
                    'actual_claims': analysis.actual_claims,
                    'profit_margin': analysis.profit_margin,
                    'risk_score': analysis.risk_score,
                    'profitability_score': analysis.profitability_score,
                    'is_profitable': analysis.profit_margin >= self.profitability_threshold
                }
                
                if analysis.profit_margin >= self.profitability_threshold:
                    profitable_policies += 1
            except Exception as e:
                logger.error(f"Error analyzing policy {policy_id}: {str(e)}")
        
        return {
            'report_timestamp': datetime.now().isoformat(),
            'portfolio_summary': {
                'total_premium': portfolio_metrics.total_premium,
                'total_expected_claims': portfolio_metrics.total_expected_claims,
                'total_actual_claims': portfolio_metrics.total_actual_claims,
                'total_profit': portfolio_metrics.total_profit,
                'profitability_ratio': portfolio_metrics.profitability_ratio,
                'combined_ratio': portfolio_metrics.combined_ratio,
                'portfolio_size': portfolio_metrics.portfolio_size,
                'risk_weighted_premium': portfolio_metrics.risk_weighted_premium,
                'return_on_risk': portfolio_metrics.return_on_risk
            },
            'policies_analysis': policy_analyses,
            'profitability_metrics': {
                'total_policies': total_policies,
                'profitable_policies': profitable_policies,
                'profitability_rate': profitable_policies / total_policies if total_policies > 0 else 0,
                'target_profitability_threshold': self.profitability_threshold
            },
            'recommendations': self._generate_recommendations(portfolio_metrics)
        }

    def _generate_recommendations(self, portfolio_metrics: PortfolioMetrics) -> List[str]:
        """
        Generate recommendations based on portfolio performance
        """
        recommendations = []
        
        if portfolio_metrics.profitability_ratio < 0.05:
            recommendations.append("Portfolio is underperforming, consider increasing premium rates by 10-15%")
        elif portfolio_metrics.profitability_ratio > 0.15:
            recommendations.append("Portfolio is highly profitable, consider more competitive rates to gain market share")
        
        if portfolio_metrics.combined_ratio > 0.9:
            recommendations.append("Combined ratio is high (over 90%), review underwriting standards")
        
        if portfolio_metrics.return_on_risk < 0.1:
            recommendations.append("Return on risk is low, improve risk selection or increase margins")
        
        if portfolio_metrics.portfolio_size < 100:
            recommendations.append("Portfolio size is small, focus on customer acquisition")
        
        return recommendations

    def optimize_portfolio_composition(self) -> Dict[str, Any]:
        """
        Optimize portfolio composition for maximum profitability
        """
        if not self.policies_db:
            return {'message': 'No policies in database to optimize'}

        # Calculate optimal risk distribution
        risk_distribution = []
        for policy_id, policy_data in self.policies_db.items():
            risk_score = np.mean(list(policy_data['risk_factors'].values())) if policy_data['risk_factors'] else 0
            profit_margin = (policy_data['premium'] - policy_data['actual_claims']) / policy_data['premium'] if policy_data['premium'] > 0 else 0
            
            risk_distribution.append({
                'policy_id': policy_id,
                'risk_score': risk_score,
                'profit_margin': profit_margin,
                'premium': policy_data['premium'],
                'retention_recommendation': 'Keep' if profit_margin >= self.profitability_threshold else 'Review'
            })

        # Sort by profit margin to identify best/worst performers
        risk_distribution.sort(key=lambda x: x['profit_margin'], reverse=True)

        # Calculate optimal portfolio mix
        high_performers = [p for p in risk_distribution if p['profit_margin'] >= 0.10]
        medium_performers = [p for p in risk_distribution if 0.05 <= p['profit_margin'] < 0.10]
        low_performers = [p for p in risk_distribution if p['profit_margin'] < 0.05]

        return {
            'total_policies': len(self.policies_db),
            'high_performers': len(high_performers),
            'medium_performers': len(medium_performers),
            'low_performers': len(low_performers),
            'top_performers': high_performers[:5],  # Top 5 performers
            'bottom_performers': low_performers[:5],  # Bottom 5 performers
            'optimization_strategy': {
                'focus_on': 'high_performers' if len(high_performers) > len(low_performers) else 'risk_adjustment',
                'recommendation': f'Focus on acquiring more policies similar to top {len(high_performers)} performers' if len(high_performers) > len(low_performers) else 'Review underwriting criteria for low performers'
            }
        }

    def update_market_conditions(self, new_conditions: Dict[str, float]) -> None:
        """
        Update market conditions that affect pricing
        
        Args:
            new_conditions: Dictionary with updated market condition values
        """
        for key, value in new_conditions.items():
            if key in self.market_conditions:
                self.market_conditions[key] = value
            else:
                logger.warning(f"Unknown market condition: {key}, adding it to the dict")
                self.market_conditions[key] = value

    def get_dynamic_pricing_factors(self, risk_profile: Dict[str, float]) -> Dict[str, float]:
        """
        Get all factors that influence dynamic pricing for a specific risk profile
        
        Args:
            risk_profile: Dictionary of risk factors
            
        Returns:
            Dictionary with all pricing factors and their impact
        """
        # Calculate risk-based adjustments
        risk_sum = sum(risk_profile.values()) if risk_profile else 0
        risk_loading = max(0.05, min(0.5, risk_sum * 0.2))
        
        # Portfolio performance factor
        portfolio_metrics = self.calculate_portfolio_metrics()
        portfolio_factor = 1.0
        if portfolio_metrics.profitability_ratio < 0.05:
            portfolio_factor = 1.15  # Increase rates due to poor portfolio performance
        elif portfolio_metrics.profitability_ratio > 0.15:
            portfolio_factor = 0.95  # Can afford to be more competitive
        
        # Market condition factor
        market_factor = (
            1 + self.market_conditions['inflation_rate'] + 
            self.market_conditions['climate_risk_premium']
        )
        
        # Competition factor
        competition_factor = 1 + (self.market_conditions['competition_intensity'] * 0.1)
        
        return {
            'base_rate_factor': 1.0,
            'risk_loading': risk_loading,
            'portfolio_performance_factor': portfolio_factor,
            'market_condition_factor': market_factor,
            'competition_factor': competition_factor,
            'total_multiplicative_factor': risk_loading * portfolio_factor * market_factor * competition_factor,
            'total_additive_factor': risk_loading + (portfolio_factor - 1) + (market_factor - 1) + (competition_factor - 1)
        }

# Global instance
dynamic_analysis_service = DynamicInsuranceAnalysisService()

# Convenience functions for API integration
def calculate_dynamic_premium(coverage_amount: float, 
                            risk_factors: Dict[str, float],
                            base_loading_factor: float = 0.20) -> Dict[str, Any]:
    """Calculate dynamic premium with comprehensive profitability analysis"""
    return dynamic_analysis_service.calculate_dynamic_premium(
        coverage_amount, risk_factors, base_loading_factor
    )

def analyze_policy_profitability(policy_id: str) -> PolicyPerformance:
    """Analyze profitability of a specific policy"""
    return dynamic_analysis_service.analyze_policy_profitability(policy_id)

def get_profitability_report() -> Dict[str, Any]:
    """Generate comprehensive profitability report"""
    return dynamic_analysis_service.get_profitability_report()

def optimize_portfolio_composition() -> Dict[str, Any]:
    """Optimize portfolio composition for maximum profitability"""
    return dynamic_analysis_service.optimize_portfolio_composition()

def get_dynamic_pricing_factors(risk_profile: Dict[str, float]) -> Dict[str, float]:
    """Get all factors that influence dynamic pricing for a specific risk profile"""
    return dynamic_analysis_service.get_dynamic_pricing_factors(risk_profile)

def add_policy_data(policy_id: str, premium: float, expected_claims: float,
                   coverage_amount: float, risk_factors: Dict[str, float],
                   duration_months: int = 12, actual_claims: float = 0.0) -> None:
    """Add policy data for analysis and learning"""
    dynamic_analysis_service.add_policy_data(
        policy_id, premium, expected_claims, coverage_amount, 
        risk_factors, duration_months, actual_claims
    )