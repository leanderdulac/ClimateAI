"""
Engine de Precificação Comercial (EPC) - Commercial Pricing Engine
Implements advanced commercial pricing with market factors, competition analysis, and profitability optimization.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

logger = logging.getLogger(__name__)


class PricingStrategy(Enum):
    """Different commercial pricing strategies"""

    MARKET_LEADING = "market_leading"
    MARKET_MATCHING = "market_matching"
    MARKET_FOLLOWING = "market_following"
    VALUE_BASED = "value_based"
    COMPETITIVE = "competitive"
    PROFIT_OPTIMIZED = "profit_optimized"


@dataclass
class CommercialPricingResult:
    """Result of commercial pricing calculation"""

    base_premium: float
    market_adjusted_premium: float
    competitive_adjusted_premium: float
    final_premium: float
    market_factor: float
    competition_factor: float
    profitability_factor: float
    target_profit_margin: float
    break_even_premium: float
    price_elasticity_impact: float
    market_position: str
    pricing_strategy: str
    competitor_analysis: Dict[str, float]
    discount_schedule: Dict[str, float]
    pricing_rationale: List[str]
    calculation_timestamp: datetime


@dataclass
class MarketData:
    """Input structure for market data"""

    competitor_rates: Dict[str, float]  # {competitor_name: rate}
    market_average_rate: float
    market_std_rate: float
    market_growth_rate: float
    market_size: int
    market_penetration: float
    economic_indicators: Dict[str, float]  # {'inflation': 0.05, 'gdp_growth': 0.03}
    regulatory_factors: Dict[str, float]
    seasonal_factors: Dict[str, float]  # {'summer': 1.1, 'winter': 1.05}
    region_premiums: Dict[str, float]
    customer_segments: Dict[str, Dict[str, float]]  # Demographics by segment


@dataclass
class RiskAdjustedPremium:
    """Risk-adjusted premium from upstream modules"""

    actuarial_premium: float
    climate_risk_adjustment: float
    total_adjusted_premium: float
    risk_score: float
    risk_components: Dict[str, float]


class EPEModuleService:
    """
    Commercial pricing engine that adjusts actuarial premiums based on:
    - Market conditions
    - Competitive landscape
    - Business strategy
    - Customer value proposition
    - Profitability targets
    """

    def __init__(self):
        self.pricing_strategies = {
            PricingStrategy.MARKET_LEADING: {"premium": 0.10, "aggressive": True},
            PricingStrategy.MARKET_MATCHING: {"premium": 0.00, "aggressive": False},
            PricingStrategy.MARKET_FOLLOWING: {"premium": -0.05, "aggressive": False},
            PricingStrategy.VALUE_BASED: {"premium": 0.15, "aggressive": True},
            PricingStrategy.COMPETITIVE: {"premium": -0.02, "aggressive": True},
            PricingStrategy.PROFIT_OPTIMIZED: {"premium": 0.08, "aggressive": False},
        }

        self.competitive_weights = {
            "price_positioning": 0.4,
            "market_share": 0.3,
            "brand_strength": 0.2,
            "service_quality": 0.1,
        }

        self.elasticity_factors = {
            "price_elasticity": -0.3,  # -0.3 means 30% demand decrease for 100% price increase
            "income_elasticity": 0.5,  # Normal goods, positive correlation
            "cross_elasticity": 0.1,  # Small positive correlation with substitutes
        }

        self.profitability_targets = {
            "minimum_margin": 0.05,  # 5% minimum
            "target_margin": 0.15,  # 15% target
            "maximum_margin": 0.30,  # 30% maximum for regulatory/compliance reasons
        }

    def calculate_commercial_pricing(
        self,
        risk_adjusted_premium: RiskAdjustedPremium,
        market_data: MarketData,
        pricing_strategy: PricingStrategy = PricingStrategy.MARKET_MATCHING,
        target_volume: Optional[float] = None,
    ) -> CommercialPricingResult:
        """
        Calculate commercial pricing based on risk-adjusted premium and market factors.

        Args:
            risk_adjusted_premium: Risk-adjusted premium from upstream modules
            market_data: Current market conditions and competitor data
            pricing_strategy: Desired pricing strategy
            target_volume: Target volume of policies (affects pricing strategy)

        Returns:
            CommercialPricingResult with full pricing breakdown
        """
        # Start with the base risk-adjusted premium from upstream
        base_premium = risk_adjusted_premium.total_adjusted_premium

        # Calculate market adjustment
        market_factor = self._calculate_market_adjustment(market_data)

        # Calculate competition adjustment
        competition_factor, competitor_analysis = (
            self._calculate_competition_adjustment(
                market_data.competitor_rates, market_data.market_average_rate
            )
        )

        # Calculate profitability factor
        profitability_factor, target_margin = self._calculate_profitability_factor(
            base_premium, market_data.economic_indicators
        )

        # Apply strategy-specific adjustments
        strategy_adjustment = self.pricing_strategies[pricing_strategy]["premium"]

        # Calculate market-adjusted premium
        market_adjusted = base_premium * (1 + market_factor)

        # Calculate competitive-adjusted premium
        competitive_adjusted = market_adjusted * (1 + competition_factor)

        # Apply strategy adjustment
        strategized_premium = competitive_adjusted * (1 + strategy_adjustment)

        # Apply profitability factor
        final_premium = strategized_premium * (1 + profitability_factor)

        # Calculate break-even point (where no profit/loss occurs)
        break_even = self._calculate_break_even_point(base_premium, market_data)

        # Calculate price elasticity impact if target volume provided
        elasticity_impact = self._calculate_elasticity_impact(
            final_premium, base_premium, target_volume
        )

        # Determine market position
        market_position = self._determine_market_position(
            final_premium, market_data.market_average_rate
        )

        # Calculate discount schedule
        discount_schedule = self._calculate_discount_schedule(final_premium)

        # Generate pricing rationale
        rationale = self._generate_pricing_rationale(
            pricing_strategy,
            market_factor,
            competition_factor,
            profitability_factor,
            final_premium,
            base_premium,
        )

        return CommercialPricingResult(
            base_premium=base_premium,
            market_adjusted_premium=market_adjusted,
            competitive_adjusted_premium=competitive_adjusted,
            final_premium=final_premium,
            market_factor=market_factor,
            competition_factor=competition_factor,
            profitability_factor=profitability_factor,
            target_profit_margin=target_margin,
            break_even_premium=break_even,
            price_elasticity_impact=elasticity_impact,
            market_position=market_position,
            pricing_strategy=pricing_strategy.value,
            competitor_analysis=competitor_analysis,
            discount_schedule=discount_schedule,
            pricing_rationale=rationale,
            calculation_timestamp=datetime.now(),
        )

    def _calculate_market_adjustment(self, market_data: MarketData) -> float:
        """Calculate market-based adjustments"""
        # Economic indicators adjustment
        inflation_rate = market_data.economic_indicators.get("inflation", 0.03)
        gdp_growth = market_data.economic_indicators.get("gdp_growth", 0.02)

        # Market growth adjustment
        market_growth_factor = market_data.market_growth_rate * 0.3

        # Seasonal adjustment
        seasonal_factor = 0.0
        current_month = datetime.now().month
        if current_month in [11, 12, 1, 2]:  # Winter months
            seasonal_factor = market_data.seasonal_factors.get("winter", 0.05)
        elif current_month in [6, 7, 8]:  # Summer months
            seasonal_factor = market_data.seasonal_factors.get("summer", 0.02)

        # Regional adjustment
        region_premium = market_data.region_premiums.get("default", 0.03)

        # Calculate total market adjustment
        market_adjustment = (
            inflation_rate * 0.5  # Inflation has strong impact
            + gdp_growth * 0.2  # Economic growth has moderate impact
            + market_growth_factor
            + seasonal_factor
            + region_premium
        )

        return market_adjustment

    def _calculate_competition_adjustment(
        self, competitor_rates: Dict[str, float], market_average: float
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate competition-based adjustments"""
        if not competitor_rates:
            return 0.05, {
                "market_position": "n/a",
                "avg_competitor_rate": market_average,
            }

        # Calculate competitor statistics
        competitor_values = list(competitor_rates.values())
        avg_competitor_rate = np.mean(competitor_values)
        min_competitor_rate = min(competitor_values)
        max_competitor_rate = max(competitor_values)

        # Determine our market position vs competitors
        if market_average <= min_competitor_rate:
            market_position = "market_leader"
            position_factor = -0.05  # Can charge premium if leading
        elif market_average >= max_competitor_rate:
            market_position = "market_follower"
            position_factor = 0.08  # Need to be more competitive if following
        else:
            market_position = "market_competitor"
            position_factor = 0.0  # Neutral if in middle

        # Calculate competitive pressure index
        # Higher variance in competitor rates means more competitive pressure
        rate_variance = np.var(competitor_values) if len(competitor_values) > 1 else 0
        competitive_pressure = min(
            0.1,
            (
                rate_variance / np.mean(competitor_values)
                if np.mean(competitor_values) > 0
                else 0
            ),
        )

        # Weight by competitor market share or importance
        total_competitor_weight = len(competitor_values)  # Simplified weighting
        competition_factor = position_factor + (competitive_pressure * 0.5)

        competitor_analysis = {
            "market_position": market_position,
            "avg_competitor_rate": avg_competitor_rate,
            "min_competitor_rate": min_competitor_rate,
            "max_competitor_rate": max_competitor_rate,
            "competitor_rate_std": np.std(competitor_values),
            "competitive_pressure_index": competitive_pressure,
            "number_competitors": len(competitor_values),
        }

        return competition_factor, competitor_analysis

    def _calculate_profitability_factor(
        self, base_premium: float, economic_indicators: Dict[str, float]
    ) -> Tuple[float, float]:
        """Calculate profitability-based adjustments"""
        # Determine target margin based on economic conditions
        inflation_rate = economic_indicators.get("inflation", 0.03)
        target_margin = self.profitability_targets["target_margin"]

        # Adjust target margin based on inflation (higher inflation may require higher margins)
        adjusted_target_margin = min(
            self.profitability_targets["maximum_margin"],
            target_margin + (inflation_rate * 0.5),  # Inflation adjustment
        )

        # Calculate required profitability adjustment
        required_profit = base_premium * adjusted_target_margin

        # Convert to premium factor
        profitability_factor = (
            required_profit / base_premium if base_premium > 0 else 0.15
        )

        return profitability_factor, adjusted_target_margin

    def _calculate_break_even_point(
        self, base_premium: float, market_data: MarketData
    ) -> float:
        """Calculate break-even premium point"""
        # Break-even includes expenses, claims, and minimum required profit
        expense_ratio = 0.25  # Industry average expense ratio
        minimum_profit_ratio = 0.02  # Minimum acceptable profit

        break_even = base_premium * (1 + expense_ratio + minimum_profit_ratio)
        return break_even

    def _calculate_elasticity_impact(
        self,
        final_premium: float,
        base_premium: float,
        target_volume: Optional[float] = None,
    ) -> float:
        """Calculate impact of price elasticity on demand/volume"""
        if target_volume is None:
            return 0.0

        # Calculate price change ratio
        if base_premium > 0:
            price_change_ratio = (final_premium - base_premium) / base_premium
        else:
            price_change_ratio = 0.0

        # Apply price elasticity
        elasticity = self.elasticity_factors["price_elasticity"]
        demand_change = price_change_ratio * elasticity

        # Impact is calculated as potential volume change due to price
        return demand_change

    def _determine_market_position(
        self, final_premium: float, market_average: float
    ) -> str:
        """Determine market position relative to average"""
        if market_average == 0:
            return "n/a"

        premium_ratio = final_premium / market_average

        if premium_ratio < 0.9:
            return "low_priced"
        elif premium_ratio < 1.1:
            return "competitive"
        elif premium_ratio < 1.3:
            return "premium"
        else:
            return "luxury/high-end"

    def _calculate_discount_schedule(self, final_premium: float) -> Dict[str, float]:
        """Calculate various discount options"""
        return {
            "annual_payment": final_premium * 0.97,  # 3% discount for annual payment
            "multi_policy": final_premium * 0.95,  # 5% discount for multiple policies
            "loyalty_1_year": final_premium * 0.98,  # 2% discount for 1+ years
            "loyalty_3_year": final_premium * 0.95,  # 5% discount for 3+ years
            "safe_driver": final_premium * 0.90,  # 10% discount for safe behavior
            "early_bird": final_premium * 0.99,  # 1% discount for early renewal
        }

    def _generate_pricing_rationale(
        self,
        pricing_strategy: PricingStrategy,
        market_factor: float,
        competition_factor: float,
        profitability_factor: float,
        final_premium: float,
        base_premium: float,
    ) -> List[str]:
        """Generate rationale for pricing decisions"""
        rationale = []

        rationale.append(f"Base pricing strategy: {pricing_strategy.value}")
        rationale.append(f"Market conditions adjustment: {market_factor:.1%}")
        rationale.append(f"Competition-based adjustment: {competition_factor:.1%}")
        rationale.append(f"Profitability requirement: {profitability_factor:.1%}")

        if final_premium > base_premium:
            rationale.append("Premium adjusted upward to meet commercial objectives")
        else:
            rationale.append("Premium adjusted downward for competitive positioning")

        # Add specific strategy rationale
        if pricing_strategy == PricingStrategy.MARKET_LEADING:
            rationale.append("Premium pricing strategy for market leadership")
        elif pricing_strategy == PricingStrategy.COMPETITIVE:
            rationale.append("Aggressive pricing to gain market share")
        elif pricing_strategy == PricingStrategy.PROFIT_OPTIMIZED:
            rationale.append("Focus on maximum profitability optimization")

        return rationale

    def optimize_pricing_for_volume(
        self, risk_adjusted_premium: RiskAdjustedPremium, market_data: MarketData
    ) -> float:
        """
        Optimize pricing for target volume considering elasticity

        Args:
            risk_adjusted_premium: Input risk-adjusted premium
            market_data: Current market conditions

        Returns:
            Optimized premium for maximum volume-profit balance
        """
        base_premium = risk_adjusted_premium.total_adjusted_premium

        def objective_function(discount_factor):
            """Objective: maximize (volume * profit per policy)"""
            discounted_premium = base_premium * (1 - discount_factor)

            # Calculate estimated volume based on elasticity
            price_ratio = discounted_premium / base_premium if base_premium > 0 else 1.0
            elasticity = self.elasticity_factors["price_elasticity"]
            volume_multiplier = 1 + (1 - price_ratio) * abs(
                elasticity
            )  # Lower price, higher volume

            # Calculate profit per policy
            profit_per_policy = discounted_premium - (
                base_premium * 0.7
            )  # Simplified cost structure

            # Objective: maximize revenue (volume * price)
            if profit_per_policy > 0:
                return -(
                    volume_multiplier * discounted_premium
                )  # Negative for minimization
            else:
                return float("inf")  # Invalid if unprofitable

        # Optimize discount (between 0 and 30%)
        result = minimize(
            objective_function, x0=[0.1], bounds=[(0.0, 0.3)], method="L-BFGS-B"
        )

        optimal_discount = result.x[0] if result.success else 0.1
        optimal_premium = base_premium * (1 - optimal_discount)

        # Ensure minimum profitability
        min_profitable_premium = base_premium * 1.05  # At least 5% profit
        return max(optimal_premium, min_profitable_premium)

    def calculate_dynamic_pricing_factors(
        self, customer_profile: Dict[str, Any], policy_features: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate dynamic pricing factors based on customer and policy characteristics

        Args:
            customer_profile: Customer demographic and behavioral data
            policy_features: Specific policy characteristics

        Returns:
            Dictionary of dynamic pricing factors
        """
        factors = {}

        # Customer-based factors
        customer_risk_score = customer_profile.get("risk_score", 0.5)
        loyalty_years = customer_profile.get("loyalty_years", 0)
        claim_history = customer_profile.get("num_claims_past_3_years", 0)

        # Apply customer scoring
        customer_factor = 0.1 * customer_risk_score  # Higher risk = higher premium
        if loyalty_years > 0:
            customer_factor -= min(0.15, loyalty_years * 0.02)  # Loyalty discount
        if claim_history > 0:
            customer_factor += min(0.2, claim_history * 0.05)  # Claim loading

        factors["customer_factor"] = customer_factor

        # Policy feature factors
        coverage_limit = policy_features.get("coverage_limit", 100000)
        deductible = policy_features.get("deductible", 1000)
        policy_term = policy_features.get("term_years", 1)

        # Coverage-based loading
        coverage_factor = max(
            0.0, (coverage_limit - 100000) / 1000000 * 0.05
        )  # 5% per million above 100k
        factors["coverage_factor"] = coverage_factor

        # Deductible incentive (higher deductible = lower premium)
        deductible_factor = -(
            min(0.15, (deductible - 500) / 5000 * 0.15)
        )  # Up to 15% discount
        factors["deductible_factor"] = deductible_factor

        # Term length factor
        term_factor = (
            0.02 * (policy_term - 1) if policy_term > 1 else 0
        )  # Multi-year discount
        factors["term_factor"] = term_factor

        return factors

    def get_pricing_strategy_recommendation(
        self, market_data: MarketData, portfolio_metrics: Dict[str, float]
    ) -> PricingStrategy:
        """
        Recommend optimal pricing strategy based on market conditions and portfolio metrics

        Args:
            market_data: Current market conditions
            portfolio_metrics: Current portfolio performance metrics

        Returns:
            Recommended pricing strategy
        """
        # Get market indicators
        market_growth = market_data.market_growth_rate
        market_concentration = (
            len(market_data.competitor_rates) if market_data.competitor_rates else 10
        )
        market_averages = market_data.market_average_rate

        # Get portfolio indicators
        portfolio_profitability = portfolio_metrics.get("profitability_ratio", 0.10)
        market_share = portfolio_metrics.get("market_share", 0.05)
        loss_ratio = portfolio_metrics.get("loss_ratio", 0.70)

        # Strategy decision logic
        if portfolio_profitability < 0.05:  # Unprofitable portfolio
            return PricingStrategy.PROFIT_OPTIMIZED
        elif (
            market_share < 0.03 and market_growth > 0.05
        ):  # Small player in growing market
            return PricingStrategy.COMPETITIVE
        elif market_concentration < 5:  # Few competitors (monopoly-like)
            return PricingStrategy.MARKET_LEADING
        elif loss_ratio > 0.85:  # High loss ratio, need to improve
            return PricingStrategy.PROFIT_OPTIMIZED
        else:
            return PricingStrategy.MARKET_MATCHING  # Default strategy


# Global instance
epe_module_service = EPEModuleService()


def calculate_commercial_pricing(
    risk_adjusted_premium: RiskAdjustedPremium,
    market_data: MarketData,
    pricing_strategy: PricingStrategy = PricingStrategy.MARKET_MATCHING,
) -> CommercialPricingResult:
    """Convenience function to calculate commercial pricing"""
    return epe_module_service.calculate_commercial_pricing(
        risk_adjusted_premium, market_data, pricing_strategy
    )


def optimize_pricing_for_volume(
    risk_adjusted_premium: RiskAdjustedPremium, market_data: MarketData
) -> float:
    """Convenience function to optimize pricing for volume"""
    return epe_module_service.optimize_pricing_for_volume(risk_adjusted_premium, market_data)


def calculate_dynamic_pricing_factors(
    customer_profile: Dict[str, Any], policy_features: Dict[str, Any]
) -> Dict[str, float]:
    """Convenience function to calculate dynamic pricing factors"""
    return epe_module_service.calculate_dynamic_pricing_factors(
        customer_profile, policy_features
    )


def get_pricing_strategy_recommendation(
    market_data: MarketData, portfolio_metrics: Dict[str, float]
) -> PricingStrategy:
    """Convenience function to get pricing strategy recommendation"""
    return epe_module_service.get_pricing_strategy_recommendation(
        market_data, portfolio_metrics
    )
