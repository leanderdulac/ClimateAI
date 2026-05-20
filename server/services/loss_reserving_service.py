"""
Loss Reserving Module - Mack's Formula and Advanced Methods

Implements actuarial loss reserving methods for climate insurance:
- Mack's Formula (distribution-free chain ladder)
- Bornhuetter-Ferguson Method
- Frequency-Severity Method
- Bootstrap Reserving

Referências:
- Mack, T. (1993). "Distribution-free Calculation of the Standard Error of Chain Ladder Reserve Estimates"
- Wüthrich, M. (2008). "Bayesian Loss Reserving"
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class ReservingMethod(str, Enum):
    """Available reserving methods"""
    CHAIN_LADDER = "chain_ladder"
    MACK = "mack"
    BORNHUETTER_FERGUSON = "bornhuetter_ferguson"
    FREQUENCY_SEVERITY = "frequency_severity"
    BOOTSTRAP = "bootstrap"


@dataclass
class TriangleData:
    """Loss development triangle data"""
    data: np.ndarray  # 2D array (accident years x development periods)
    accident_years: List[int]
    development_periods: List[int]
    cumulative: bool = True
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, value_col: str = 'value') -> 'TriangleData':
        """Create triangle from DataFrame"""
        # Assume columns: accident_year, development_period, value
        accident_years = sorted(df['accident_year'].unique().tolist())
        development_periods = sorted(df['development_period'].unique().tolist())
        
        # Pivot to triangle matrix
        triangle = df.pivot(
            index='accident_year',
            columns='development_period',
            values=value_col
        ).reindex(index=accident_years, columns=development_periods)
        
        return cls(
            data=triangle.values,
            accident_years=accident_years,
            development_periods=development_periods,
            cumulative=True,
        )
    
    def to_incremental(self) -> np.ndarray:
        """Convert cumulative triangle to incremental"""
        if not self.cumulative:
            return self.data.copy()
        
        incremental = self.data.copy()
        incremental[:, 1:] = self.data[:, 1:] - self.data[:, :-1]
        return incremental
    
    def get_latest_cumulative(self) -> np.ndarray:
        """Get latest cumulative values for each accident year"""
        if self.cumulative:
            # Get last available value for each row
            latest = []
            for i, row in enumerate(self.data):
                # Find last non-NaN value
                valid_values = row[~np.isnan(row)]
                if len(valid_values) > 0:
                    latest.append(valid_values[-1])
                else:
                    latest.append(np.nan)
            return np.array(latest)
        else:
            # Sum incremental to get cumulative
            return np.nansum(self.data, axis=1)


@dataclass
class MackResult:
    """Result from Mack's Formula calculation"""
    method: str
    ultimate_losses: float
    current_losses: float
    reserves: float
    standard_error: float
    coefficient_of_variation: float
    development_factors: List[float]
    sigma_k: List[float]  # Process variance for each period
    tau_k: List[float]  # Variance of development factors
    confidence_intervals: Dict[str, Tuple[float, float]]
    run_off_triangle: Optional[np.ndarray] = None
    ibnr: float = 0.0  # Incurred But Not Reported


@dataclass
class BornhuetterFergusonResult:
    """Result from Bornhuetter-Ferguson method"""
    method: str
    ultimate_losses: float
    current_losses: float
    reserves: float
    prior_ultimate: float  # Initial estimate
    reported_percentage: float
    ibnr: float
    credibility_weight: float  # Weight given to actual experience


@dataclass
class BootstrapReserveResult:
    """Result from bootstrap reserving"""
    method: str
    point_estimate: float
    mean_bootstrap: float
    standard_error: float
    percentiles: Dict[str, float]  # P10, P25, P50, P75, P90, P95, P99
    reserve_distribution: np.ndarray
    n_simulations: int


@dataclass
class ComprehensiveReservingResult:
    """Comprehensive result combining all methods"""
    method_results: Dict[str, Any]
    recommended_reserve: float
    reserve_range: Tuple[float, float]
    method_weights: Dict[str, float]
    diagnostic_metrics: Dict[str, Any]
    timestamp: str


class LossReservingService:
    """
    Comprehensive loss reserving service implementing multiple actuarial methods.
    """
    
    def __init__(self):
        self.default_confidence_levels = [0.75, 0.80, 0.85, 0.90, 0.95, 0.99]
        
    def calculate_mack_reserve(
        self,
        triangle: TriangleData,
        confidence_level: float = 0.95,
    ) -> MackResult:
        """
        Calculate reserves using Mack's Formula (distribution-free chain ladder)
        
        Mack's Formula provides:
        - Point estimate of reserves (same as chain ladder)
        - Standard error of reserves
        - Prediction interval
        
        Args:
            triangle: Cumulative loss development triangle
            confidence_level: Confidence level for intervals
            
        Returns:
            MackResult with reserves and standard error
        """
        logger.info("Calculating Mack's Formula reserves")
        
        if not triangle.cumulative:
            raise ValueError("Mack's Formula requires cumulative triangle")
        
        data = triangle.data
        n_accidents = data.shape[0]
        n_periods = data.shape[1]
        
        # Step 1: Calculate development factors (f_k)
        development_factors = []
        sigma_k = []  # Process variance
        tau_k = []  # Variance of development factors
        
        for k in range(n_periods - 1):
            # Get values for development period k to k+1
            numerator = 0.0
            denominator = 0.0
            
            for i in range(n_accidents - k):
                if not np.isnan(data[i, k]) and not np.isnan(data[i, k + 1]):
                    numerator += data[i, k + 1]
                    denominator += data[i, k]
            
            if denominator > 0:
                f_k = numerator / denominator
            else:
                f_k = 1.0
            
            development_factors.append(f_k)
            
            # Calculate variance parameter sigma_k^2
            if n_accidents - k - 1 > 1:
                var_sum = 0.0
                weight_sum = 0.0
                
                for i in range(n_accidents - k - 1):
                    if not np.isnan(data[i, k]) and data[i, k] > 0:
                        predicted = data[i, k] * f_k
                        actual = data[i, k + 1]
                        weight = data[i, k]
                        var_sum += weight * ((actual / data[i, k] - f_k) ** 2)
                        weight_sum += weight
                
                if weight_sum > 0:
                    sigma_k_sq = var_sum / (n_accidents - k - 2) if n_accidents - k - 2 > 0 else 0
                else:
                    sigma_k_sq = 0.0
            else:
                sigma_k_sq = 0.0
            
            sigma_k.append(sigma_k_sq)
            
            # Calculate variance of development factor tau_k^2
            if denominator > 0:
                tau_k_sq = sigma_k_sq / denominator
            else:
                tau_k_sq = 0.0
            
            tau_k.append(tau_k_sq)
        
        # Step 2: Calculate ultimate losses for each accident year
        ultimate_losses = []
        run_off_triangle = []
        
        for i in range(n_accidents):
            # Get latest cumulative value
            latest = None
            for j in range(n_periods - 1, -1, -1):
                if not np.isnan(data[i, j]):
                    latest = data[i, j]
                    break
            
            if latest is None:
                ultimate_losses.append(np.nan)
                continue
            
            # Project to ultimate using development factors
            ultimate = latest
            for k in range(len(triangle.development_periods) - 1 - (n_periods - 1) + i, len(development_factors)):
                if k < len(development_factors):
                    ultimate *= development_factors[k]
            
            ultimate_losses.append(ultimate)
            
            # Build run-off triangle (projected future values)
            row = [data[i, j] if not np.isnan(data[i, j]) else None for j in range(n_periods)]
            for j in range(n_periods, len(triangle.development_periods)):
                row.append(None)
            run_off_triangle.append(row)
        
        ultimate_losses = np.array(ultimate_losses)
        
        # Step 3: Calculate total reserves
        current_losses = triangle.get_latest_cumulative()
        total_reserves = np.nansum(ultimate_losses) - np.nansum(current_losses)
        
        # Step 4: Calculate standard error using Mack's Formula
        # Var(R) = Σ Σ C_{i,k} * τ_k^2 * Π f_j^2 + Σ (σ_k^2 / f_k^2) * (Σ C_{i,k})^2
        variance_components = []
        
        for i in range(n_accidents):
            latest = current_losses[i]
            if np.isnan(latest) or latest <= 0:
                continue
            
            # Process variance component
            process_var = 0.0
            estimation_var = 0.0
            
            for k in range(len(development_factors)):
                # Cumulative to development period k
                cum_k = latest
                for j in range(k):
                    if j < len(development_factors):
                        cum_k *= development_factors[j]
                
                # Future development factor product
                future_prod = 1.0
                for j in range(k + 1, len(development_factors)):
                    future_prod *= (development_factors[j] ** 2)
                
                process_var += cum_k * sigma_k[k] * future_prod
                estimation_var += (sigma_k[k] / (development_factors[k] ** 2)) * (cum_k ** 2)
            
            variance_components.append(process_var + estimation_var)
        
        total_variance = np.sum(variance_components)
        standard_error = np.sqrt(total_variance)
        
        # Coefficient of variation
        cv = standard_error / total_reserves if total_reserves > 0 else 0.0
        
        # Step 5: Calculate confidence intervals
        z_score = stats.norm.ppf(confidence_level)
        ci_lower = total_reserves - z_score * standard_error
        ci_upper = total_reserves + z_score * standard_error
        
        # IBNR (Incurred But Not Reported)
        ibnr = total_reserves  # Simplified: all reserves are IBNR
        
        return MackResult(
            method="mack",
            ultimate_losses=float(np.nansum(ultimate_losses)),
            current_losses=float(np.nansum(current_losses)),
            reserves=float(total_reserves),
            standard_error=float(standard_error),
            coefficient_of_variation=float(cv),
            development_factors=development_factors,
            sigma_k=sigma_k,
            tau_k=tau_k,
            confidence_intervals={
                f"{int(confidence_level*100)}%": (float(ci_lower), float(ci_upper)),
            },
            run_off_triangle=np.array(run_off_triangle, dtype=object) if run_off_triangle else None,
            ibnr=float(ibnr),
        )
    
    def calculate_bornhuetter_ferguson(
        self,
        triangle: TriangleData,
        prior_ultimate: float,
        expected_loss_ratio: float = 0.70,
    ) -> BornhuetterFergusonResult:
        """
        Calculate reserves using Bornhuetter-Ferguson method
        
        This method blends:
        - Chain ladder projection (actual experience)
        - Prior estimate (expected loss ratio)
        
        The credibility weight increases as more data becomes available.
        
        Args:
            triangle: Cumulative loss development triangle
            prior_ultimate: Initial estimate of ultimate losses
            expected_loss_ratio: Expected loss ratio for prior calculation
            
        Returns:
            BornhuetterFergusonResult
        """
        logger.info("Calculating Bornhuetter-Ferguson reserves")
        
        # Get chain ladder result for comparison
        mack_result = self.calculate_mack_reserve(triangle)
        
        # Calculate reported percentage (how much of ultimate is reported)
        current_losses = triangle.get_latest_cumulative()
        total_current = np.nansum(current_losses)
        
        # Reported percentage based on development
        development_factors = mack_result.development_factors
        total_development = np.prod(development_factors) if development_factors else 1.0
        
        reported_percentage = 1.0 / total_development
        
        # Credibility factor (Z)
        # More mature years get higher credibility
        n_periods = len(triangle.development_periods)
        credibility_weight = min(1.0, n_periods / 5.0)  # Full credibility at 5 periods
        
        # Blend prior and experience
        ultimate_bf = (
            credibility_weight * mack_result.ultimate_losses +
            (1 - credibility_weight) * prior_ultimate
        )
        
        # Calculate reserves
        reserves = ultimate_bf - total_current
        ibnr = reserves  # Simplified
        
        return BornhuetterFergusonResult(
            method="bornhuetter_ferguson",
            ultimate_losses=float(ultimate_bf),
            current_losses=float(total_current),
            reserves=float(reserves),
            prior_ultimate=float(prior_ultimate),
            reported_percentage=float(reported_percentage),
            ibnr=float(ibnr),
            credibility_weight=float(credibility_weight),
        )
    
    def calculate_frequency_severity(
        self,
        claims_data: pd.DataFrame,
        exposure: float,
    ) -> Dict[str, Any]:
        """
        Calculate reserves using frequency-severity method
        
        Args:
            claims_data: DataFrame with columns: claim_id, accident_date, reported_date, amount
            exposure: Exposure base (e.g., earned premium, number of policies)
            
        Returns:
            Dictionary with frequency and severity analysis
        """
        logger.info("Calculating Frequency-Severity reserves")
        
        # Calculate claim frequency
        n_claims = len(claims_data)
        frequency = n_claims / exposure if exposure > 0 else 0.0
        
        # Calculate claim severity
        if 'amount' in claims_data.columns:
            severity = float(claims_data['amount'].mean()) if len(claims_data) > 0 else 0.0
            severity_std = float(claims_data['amount'].std()) if len(claims_data) > 1 else 0.0
        else:
            severity = 0.0
            severity_std = 0.0
        
        # Pure premium (expected loss)
        pure_premium = frequency * severity
        
        # Expected loss
        expected_loss = pure_premium * exposure
        if len(claims_data) > 10 and 'amount' in claims_data.columns:
            # Fit lognormal for severity
            amounts = claims_data['amount'].dropna()
            if len(amounts) > 0:
                # lognorm.fit returns (shape, loc, scale)
                shape, loc, scale = stats.lognorm.fit(amounts, floc=0)
                severity_distribution = {
                    "distribution": "lognormal",
                    "shape": float(shape),
                    "loc": float(loc),
                    "scale": float(scale),
                    "mean": float(scale * np.exp(shape**2 / 2)),
                    "std": float(scale * np.sqrt((np.exp(shape**2) - 1) * np.exp(shape**2))),
                }
            else:
                severity_distribution = {}
        else:
            severity_distribution = {}
        
        return {
            "method": "frequency_severity",
            "n_claims": n_claims,
            "exposure": exposure,
            "frequency": frequency,
            "severity": severity,
            "severity_std": severity_std,
            "pure_premium": pure_premium,
            "expected_loss": expected_loss,
            "severity_distribution": severity_distribution,
        }
    
    def calculate_bootstrap_reserves(
        self,
        triangle: TriangleData,
        n_simulations: int = 1000,
        confidence_level: float = 0.95,
    ) -> BootstrapReserveResult:
        """
        Calculate reserves using bootstrap method (England & Verrall / ODP method)
        
        This provides a full distribution of reserves by calculating adjusted Pearson residuals,
        resampling them with replacement to create pseudo-triangles, projecting future losses,
        and incorporating Over-dispersed Poisson process variance via a Gamma distribution.
        
        Args:
            triangle: Cumulative loss development triangle
            n_simulations: Number of bootstrap simulations
            confidence_level: Confidence level for intervals
            
        Returns:
            BootstrapReserveResult with full distribution
        """
        logger.info(f"Calculating Bootstrap reserves with {n_simulations} simulations using ODP Pearson residuals")
        
        if not triangle.cumulative:
            raise ValueError("Bootstrap reserving requires cumulative triangle")
            
        # Get point estimate using Mack
        mack_result = self.calculate_mack_reserve(triangle)
        point_estimate = mack_result.reserves
        
        # 1. Extract incremental losses from cumulative triangle
        cum_data = triangle.data.copy()
        n_accidents, n_periods = cum_data.shape
        
        inc_data = np.zeros_like(cum_data)
        inc_data[:, 0] = cum_data[:, 0]
        inc_data[:, 1:] = cum_data[:, 1:] - cum_data[:, :-1]
        
        # 2. Get development factors (f_k) from Mack/Chain Ladder
        development_factors = mack_result.development_factors
        
        # 3. Calculate cumulative fitted values backwards from diagonal
        cum_fitted = np.zeros_like(cum_data)
        for i in range(n_accidents):
            last_idx = n_periods - 1 - i
            if last_idx < 0:
                continue
            
            # Set diagonal value
            cum_fitted[i, last_idx] = cum_data[i, last_idx]
            
            # Project backwards
            for k in range(last_idx - 1, -1, -1):
                if k < len(development_factors) and development_factors[k] > 0:
                    cum_fitted[i, k] = cum_fitted[i, k + 1] / development_factors[k]
                else:
                    cum_fitted[i, k] = cum_fitted[i, k + 1]
        
        # 4. Calculate fitted incremental values
        inc_fitted = np.zeros_like(cum_fitted)
        inc_fitted[:, 0] = cum_fitted[:, 0]
        inc_fitted[:, 1:] = cum_fitted[:, 1:] - cum_fitted[:, :-1]
        
        # 5. Calculate Pearson residuals on the upper triangle
        residuals = []
        residual_indices = []
        
        for i in range(n_accidents):
            for j in range(n_periods - i):
                actual = inc_data[i, j]
                fitted = inc_fitted[i, j]
                
                # Only compute residual if fitted is positive and valid
                if not np.isnan(actual) and not np.isnan(fitted) and fitted > 0:
                    r = (actual - fitted) / np.sqrt(fitted)
                    residuals.append(r)
                    residual_indices.append((i, j))
        
        residuals = np.array(residuals)
        N = len(residuals)
        
        # Calculate degrees of freedom: N - p
        p = n_accidents + n_periods - 1
        df = N - p
        if df <= 0:
            df = 1  # Avoid division by zero
            
        # Calculate dispersion parameter phi
        phi = np.sum(residuals ** 2) / df
        if phi <= 0:
            phi = 1.0
            
        # Calculate adjusted Pearson residuals
        adj_factor = np.sqrt(N / df)
        adj_residuals = residuals * adj_factor
        
        # Bootstrap simulation loop
        bootstrap_reserves = []
        
        for sim in range(n_simulations):
            # Resample adjusted residuals with replacement
            resampled_residuals = np.random.choice(adj_residuals, size=N, replace=True)
            
            # Construct pseudo-incremental triangle for the upper part
            pseudo_inc = np.full_like(inc_data, np.nan)
            
            res_idx = 0
            for i, j in residual_indices:
                fitted = inc_fitted[i, j]
                r_star = resampled_residuals[res_idx]
                res_idx += 1
                
                # Reconstruct cell: fitted + r* * sqrt(fitted)
                val = fitted + r_star * np.sqrt(fitted)
                pseudo_inc[i, j] = max(0.0, val)  # Floor at 0 to avoid negative claims
                
            # Reconstruct cumulative pseudo-triangle
            pseudo_cum = np.full_like(cum_data, np.nan)
            for i in range(n_accidents):
                acc_row = pseudo_inc[i, :n_periods - i]
                if len(acc_row) > 0 and not np.isnan(acc_row[0]):
                    pseudo_cum[i, 0] = acc_row[0]
                    for j in range(1, len(acc_row)):
                        pseudo_cum[i, j] = pseudo_cum[i, j - 1] + acc_row[j]
                        
            # Fit new Chain Ladder on pseudo cumulative triangle to get f_k^*
            pseudo_factors = []
            for k in range(n_periods - 1):
                numerator = 0.0
                denominator = 0.0
                for i in range(n_accidents - k - 1):
                    if not np.isnan(pseudo_cum[i, k]) and not np.isnan(pseudo_cum[i, k + 1]):
                        numerator += pseudo_cum[i, k + 1]
                        denominator += pseudo_cum[i, k]
                if denominator > 0:
                    pseudo_factors.append(numerator / denominator)
                else:
                    if k < len(development_factors):
                        pseudo_factors.append(development_factors[k])
                    else:
                        pseudo_factors.append(1.0)
                        
            # Project future cumulative losses in the lower triangle
            sim_cum = pseudo_cum.copy()
            
            for i in range(n_accidents):
                start_j = n_periods - i
                if start_j >= n_periods:
                    continue
                    
                latest_val = cum_data[i, start_j - 1]
                if np.isnan(latest_val) or latest_val <= 0:
                    latest_val = pseudo_cum[i, start_j - 1] if not np.isnan(pseudo_cum[i, start_j - 1]) else 0.0
                    
                sim_cum[i, start_j - 1] = latest_val
                
                for j in range(start_j, n_periods):
                    f_idx = j - 1
                    if f_idx < len(pseudo_factors):
                        sim_cum[i, j] = sim_cum[i, j - 1] * pseudo_factors[f_idx]
                    else:
                        sim_cum[i, j] = sim_cum[i, j - 1]
                        
            # Extract incremental projected values for the lower triangle
            sim_inc = np.zeros_like(sim_cum)
            sim_inc[:, 0] = sim_cum[:, 0]
            sim_inc[:, 1:] = sim_cum[:, 1:] - sim_cum[:, :-1]
            
            # Incorporate process variance via ODP Gamma simulation
            sim_reserve = 0.0
            for i in range(n_accidents):
                start_j = n_periods - i
                for j in range(start_j, n_periods):
                    mean_val = sim_inc[i, j]
                    if mean_val > 0 and phi > 0:
                        sim_val = np.random.gamma(shape=(mean_val / phi), scale=phi)
                    else:
                        sim_val = max(0.0, mean_val)
                    sim_reserve += sim_val
                    
            bootstrap_reserves.append(sim_reserve)
            
        bootstrap_reserves = np.array(bootstrap_reserves)
        
        if len(bootstrap_reserves) == 0:
            bootstrap_reserves = np.array([point_estimate])
            
        # Calculate statistics
        mean_bootstrap = np.mean(bootstrap_reserves)
        std_bootstrap = np.std(bootstrap_reserves)
        
        # Calculate percentiles
        percentiles = {
            "P10": float(np.percentile(bootstrap_reserves, 10)),
            "P25": float(np.percentile(bootstrap_reserves, 25)),
            "P50": float(np.percentile(bootstrap_reserves, 50)),
            "P75": float(np.percentile(bootstrap_reserves, 75)),
            "P90": float(np.percentile(bootstrap_reserves, 90)),
            "P95": float(np.percentile(bootstrap_reserves, 95)),
            "P99": float(np.percentile(bootstrap_reserves, 99)),
        }
        
        return BootstrapReserveResult(
            method="bootstrap",
            point_estimate=float(point_estimate),
            mean_bootstrap=float(mean_bootstrap),
            standard_error=float(std_bootstrap),
            percentiles=percentiles,
            reserve_distribution=bootstrap_reserves,
            n_simulations=len(bootstrap_reserves),
        )
    
    def calculate_comprehensive_reserves(
        self,
        triangle: TriangleData,
        prior_ultimate: Optional[float] = None,
        claims_data: Optional[pd.DataFrame] = None,
        exposure: Optional[float] = None,
        n_bootstrap_simulations: int = 500,
    ) -> ComprehensiveReservingResult:
        """
        Calculate comprehensive reserves using all available methods
        
        Args:
            triangle: Loss development triangle
            prior_ultimate: Prior estimate for Bornhuetter-Ferguson
            claims_data: Individual claim data for frequency-severity
            exposure: Exposure base for frequency-severity
            n_bootstrap_simulations: Number of bootstrap simulations
            
        Returns:
            ComprehensiveReservingResult combining all methods
        """
        logger.info("Calculating comprehensive reserves")
        
        method_results = {}
        reserves_estimates = []
        weights = {}
        
        # 1. Mack's Formula (primary method)
        mack_result = self.calculate_mack_reserve(triangle)
        method_results["mack"] = mack_result
        reserves_estimates.append(mack_result.reserves)
        weights["mack"] = 0.35  # Highest weight
        
        # 2. Bornhuetter-Ferguson (if prior available)
        if prior_ultimate is not None:
            bf_result = self.calculate_bornhuetter_ferguson(triangle, prior_ultimate)
            method_results["bornhuetter_ferguson"] = bf_result
            reserves_estimates.append(bf_result.reserves)
            weights["bornhuetter_ferguson"] = 0.25
        
        # 3. Frequency-Severity (if data available)
        if claims_data is not None and exposure is not None:
            fs_result = self.calculate_frequency_severity(claims_data, exposure)
            method_results["frequency_severity"] = fs_result
            # Convert pure premium to reserve estimate
            fs_reserve = fs_result["expected_loss"] - np.nansum(triangle.get_latest_cumulative())
            if fs_reserve > 0:
                reserves_estimates.append(fs_reserve)
                weights["frequency_severity"] = 0.20
        
        # 4. Bootstrap (for uncertainty quantification)
        try:
            bootstrap_result = self.calculate_bootstrap_reserves(triangle, n_bootstrap_simulations)
            method_results["bootstrap"] = bootstrap_result
            reserves_estimates.append(bootstrap_result.mean_bootstrap)
            weights["bootstrap"] = 0.20
        except Exception as e:
            logger.warning(f"Bootstrap failed: {e}")
            method_results["bootstrap"] = {"error": str(e)}
        
        # Normalize weights
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
        
        # Calculate weighted average reserve
        def get_reserve(method_result):
            """Extract reserve from any method result type"""
            if hasattr(method_result, 'reserves'):
                return method_result.reserves
            elif hasattr(method_result, 'mean_bootstrap'):
                return method_result.mean_bootstrap
            elif hasattr(method_result, 'expected_loss'):
                # Frequency-severity result
                current_losses = np.nansum(triangle.get_latest_cumulative())
                return method_result["expected_loss"] - current_losses
            else:
                return 0.0
        
        recommended_reserve = sum(
            get_reserve(method_results[k])
            for k in weights.keys()
        )
        
        # Reserve range (P10 to P90 from bootstrap if available)
        if "bootstrap" in method_results and hasattr(method_results["bootstrap"], 'percentiles'):
            reserve_range = (
                method_results["bootstrap"].percentiles["P10"],
                method_results["bootstrap"].percentiles["P90"],
            )
        else:
            # Fallback: use min/max of estimates
            reserve_range = (min(reserves_estimates), max(reserves_estimates))
        
        # Diagnostic metrics
        diagnostic_metrics = {
            "n_methods_used": len([k for k in weights.keys() if k in method_results]),
            "reserve_cv": np.std(reserves_estimates) / np.mean(reserves_estimates) if reserves_estimates else 0,
            "method_agreement": 1 - (np.std(reserves_estimates) / np.mean(reserves_estimates)) if reserves_estimates else 1,
        }
        
        from datetime import datetime
        return ComprehensiveReservingResult(
            method_results=method_results,
            recommended_reserve=float(recommended_reserve),
            reserve_range=reserve_range,
            method_weights=weights,
            diagnostic_metrics=diagnostic_metrics,
            timestamp=datetime.now().isoformat(),
        )


# Singleton instance
loss_reserving_service = LossReservingService()
