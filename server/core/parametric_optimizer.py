
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import pandas as pd
import numpy as np
from core.parametric_actuary import (
    RainfallIndexContract,
    compute_historical_payouts,
    expected_loss_and_metrics,
    basis_risk_metrics
)

@dataclass
class OptimizationResult:
    trigger_mm: float
    exhaustion_mm: float
    aal: float
    false_negative_rate: float
    false_positive_rate: float
    correlation: float
    payout_frequency: float

class ParametricOptimizer:
    def __init__(self, df_rain: pd.DataFrame, area_id: str):
        self.df_rain = df_rain
        self.area_id = area_id
        # Pre-calculate years for performance
        self.years = sorted(df_rain['date'].dt.year.unique())

    def optimize_grid(
        self,
        base_contract: RainfallIndexContract,
        target_aal_min: float,
        target_aal_max: float,
        df_actual_losses: Optional[pd.DataFrame] = None,
        trigger_range: Tuple[float, float, float] = (50, 200, 10), # start, stop, step
        exhaustion_add_range: Tuple[float, float, float] = (50, 300, 25) # relative to trigger
    ) -> List[OptimizationResult]:
        """
        Performs a grid search to find optimal T/E configurations.
        """
        results = []
        
        triggers = np.arange(*trigger_range)
        exhaustion_adds = np.arange(*exhaustion_add_range)
        
        for t in triggers:
            for add in exhaustion_adds:
                e = t + add
                
                # Update contract parameters
                # Note: We create a new instance or copy to avoid side effects if not careful, 
                # but dataclass replace is cleaner. For speed, we just mutate a temporary contract or init new one.
                # Init new one is safer.
                candidate_contract = RainfallIndexContract(
                    area_id=self.area_id,
                    start_date=base_contract.start_date,
                    end_date=base_contract.end_date,
                    trigger_mm=float(t),
                    exhaustion_mm=float(e),
                    max_payout=base_contract.max_payout,
                    index_type=base_contract.index_type,
                    payment_shape=base_contract.payment_shape
                )
                
                # Run Simulation
                df_payouts = compute_historical_payouts(self.df_rain, candidate_contract, self.years)
                metrics = expected_loss_and_metrics(df_payouts)
                aal = metrics['AAL']
                
                # Filter by AAL constraint first (fastest)
                if not (target_aal_min <= aal <= target_aal_max):
                    continue
                    
                # Calculate Basis Risk if data available
                fn, fp, corr = 0.0, 0.0, 0.0
                if df_actual_losses is not None and not df_actual_losses.empty:
                    br = basis_risk_metrics(df_payouts, df_actual_losses)
                    fn = br.get('false_negative_rate', 0.0)
                    fp = br.get('false_positive_rate', 0.0)
                    corr = br.get('corr_payout_vs_loss', 0.0)
                
                # Sanitize
                def sanitize(v): return 0.0 if np.isnan(v) else float(v)

                results.append(OptimizationResult(
                    trigger_mm=float(t),
                    exhaustion_mm=float(e),
                    aal=sanitize(aal),
                    false_negative_rate=sanitize(fn),
                    false_positive_rate=sanitize(fp),
                    correlation=sanitize(corr),
                    payout_frequency=sanitize(metrics['p_positive'])
                ))
                
        # Sort by False Negative Rate (ascending) then by Correlation (descending)
        results.sort(key=lambda x: (x.false_negative_rate, -x.correlation))
        
        return results
