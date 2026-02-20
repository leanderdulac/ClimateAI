from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any
import numpy as np
import pandas as pd

# =========================
# 1. Contract Model
# =========================

@dataclass
class RainfallIndexContract:
    area_id: str
    start_date: str              # 'MM-DD'
    end_date: str                # 'MM-DD'
    trigger_mm: float            # T – trigger level
    exhaustion_mm: float         # E – exhaustion level
    max_payout: float            # Parametric Sum Insured (R$)
    index_type: str = "max_3day" # 'max_3day' or 'cum_period'
    payment_shape: str = "linear" # 'linear' or 'step'
    step_levels: Optional[List[Tuple[float, float]]] = None
    # step_levels = [(threshold_mm, relative_payout_0_to_1), ...] sorted by threshold

    def compute_index_for_period(self, df_area: pd.DataFrame, year: int) -> float:
        """
        Calculates the index value for a specific year using robust date filtering.
        df_area: dataframe filtered for corresponding area_id, with columns ['date', 'rain_mm'].
        """
        df_year = df_area.copy()
        df_year['date'] = pd.to_datetime(df_year['date'])
        
        # Robustly handle start/end dates even if they come as YYYY-MM-DD or MM-DD
        # We take the last 5 characters to ensure we get MM-DD
        start_md = self.start_date[-5:]
        end_md = self.end_date[-5:]
        
        start_dt = pd.to_datetime(f"{year}-{start_md}")
        end_dt = pd.to_datetime(f"{year}-{end_md}")
        
        # Cross-year handling (e.g. Start Oct, End Apr)
        # If start > end in MM-DD, it implies the period crosses the year boundary.
        # User logic implies single calendar year filtering:
        # (df_year['date'] >= ...) & (df_year['date'] <= ...)
        # We will stick to that for now to match user snippet exactly.
        
        mask = (df_year['date'] >= start_dt) & (df_year['date'] <= end_dt)
        df_year = df_year[mask]

        if df_year.empty:
            return np.nan

        if self.index_type == "max_3day":
            rain = df_year.set_index('date')['rain_mm'].sort_index()
            rolling_sum = rain.rolling(window=3).sum()
            return float(rolling_sum.max())
        elif self.index_type == "cum_period":
            return float(df_year['rain_mm'].sum())
        else:
            raise ValueError(f"Unknown index_type: {self.index_type}")

    def index_to_payout_ratio(self, index_value: float) -> float:
        """
        Converts index value to payout fraction (0–1).
        """
        if np.isnan(index_value):
            return 0.0

        if self.payment_shape == "linear":
            if index_value <= self.trigger_mm:
                return 0.0
            elif index_value >= self.exhaustion_mm:
                return 1.0
            else:
                return (index_value - self.trigger_mm) / (self.exhaustion_mm - self.trigger_mm)

        elif self.payment_shape == "step":
            if not self.step_levels:
                raise ValueError("step_levels must be defined for payment_shape='step'")
            payout_ratio = 0.0
            for limit, level in sorted(self.step_levels, key=lambda x: x[0]):
                if index_value >= limit:
                    payout_ratio = level
                else:
                    break
            return payout_ratio
        else:
            raise ValueError(f"Unknown payment_shape: {self.payment_shape}")

    def index_to_payout_amount(self, index_value: float) -> float:
        return self.index_to_payout_ratio(index_value) * self.max_payout


# =========================
# 2. Backtesting Functions
# =========================

def compute_historical_payouts(
    df_rain: pd.DataFrame,
    contract: RainfallIndexContract,
    years: List[int]
) -> pd.DataFrame:
    """
    Calculates historical index and payout per year.
    """
    df_area = df_rain[df_rain['area_id'] == contract.area_id].copy()
    results = []
    for y in years:
        idx_val = contract.compute_index_for_period(df_area, y)
        payout = contract.index_to_payout_amount(idx_val)
        results.append({"year": y, "index": idx_val, "payout": payout})
    return pd.DataFrame(results)


def expected_loss_and_metrics(df_payouts: pd.DataFrame) -> Dict[str, float]:
    """
    Calculates AAL and frequency metrics.
    """
    df = df_payouts.dropna(subset=['payout'])
    aal = df['payout'].mean()
    p_zero = (df['payout'] == 0).mean()
    p_positive = (df['payout'] > 0).mean()
    p_full = (df['payout'] >= df['payout'].max()).mean()
    
    return {
        "AAL": float(aal),
        "p_zero": float(p_zero),
        "p_positive": float(p_positive),
        "p_full": float(p_full),
        "years_used": int(df.shape[0]),
    }

# =========================
# 3. Basis Risk
# =========================

def basis_risk_metrics(
    df_payouts: pd.DataFrame,
    df_actual_loss: pd.DataFrame,
    loss_col: str = "actual_loss_ratio",
    high_loss_threshold: float = 0.3,
    low_loss_threshold: float = 0.05
) -> Dict[str, float]:
    """
    Correlation and False Pos/Neg analysis.
    """
    df = pd.merge(df_payouts, df_actual_loss, on="year", how="inner")
    if df.empty:
        # Avoid crashing if no intersection, just return NaNs
        return {
            "corr_payout_vs_loss": np.nan,
            "false_negative_rate": np.nan,
            "false_positive_rate": np.nan,
            "n_years": 0,
        }

    corr = float(df['payout'].corr(df[loss_col])) if df[loss_col].std() > 0 else np.nan

    df['severe_loss'] = df[loss_col] >= high_loss_threshold
    df['low_loss'] = df[loss_col] <= low_loss_threshold
    df['pays'] = df['payout'] > 0

    fn = ((df['severe_loss']) & (~df['pays'])).mean()
    fp = ((df['low_loss']) & (df['pays'])).mean()

    # Sanitize NaNs for JSON serialization
    def sanitizer(val):
        return 0.0 if pd.isna(val) else float(val)

    return {
        "corr_payout_vs_loss": sanitizer(corr),
        "false_negative_rate": sanitizer(fn),
        "false_positive_rate": sanitizer(fp),
        "n_years": int(df.shape[0]),
    }

# =========================
# 4. Distribution Analysis (VaR/TVaR/EP)
# =========================

def calculate_ep_curve(df_payouts: pd.DataFrame, percentis=None) -> pd.DataFrame:
    """
    EP (Exceedance Probability) Curve.
    """
    if percentis is None:
        percentis = np.arange(0.5, 100.0, 0.5)
    
    payouts = df_payouts['payout'].dropna().sort_values(ascending=True)
    n = len(payouts)
    
    occ_ep = []
    for p in percentis:
        # Percentile logic
        idx = int(np.ceil((100 - p) / 100 * n)) - 1
        idx = max(0, min(idx, n - 1))
        occ_ep.append(payouts.iloc[idx])
    
    return pd.DataFrame({
        'prob_not_exceed_pct': percentis,
        'prob_exceedance': 100 - percentis,
        'OCC_EP': occ_ep,
        # AEP assumed same as OCC for annual aggregate in single event contracts
        'AEP_EP': occ_ep 
    })

def calculate_var_tvar(df_payouts: pd.DataFrame, alpha=0.95) -> Dict[str, float]:
    """
    VaR and TVaR.
    """
    payouts = df_payouts['payout'].dropna().sort_values()
    if payouts.empty:
        return {'alpha': alpha, 'VaR': 0.0, 'TVaR': 0.0, 'n_years': 0}

    n = len(payouts)
    
    idx_var = int(np.floor(alpha * n))
    idx_var = min(idx_var, n - 1)
    var = payouts.iloc[idx_var]
    
    tvar = payouts.iloc[idx_var:].mean()
    
    return {
        'alpha': alpha,
        'VaR': float(var),
        'TVaR': float(tvar),
        'n_years': n
    }

# =========================
# 5. Reinsurance
# =========================

@dataclass
class ReinsuranceLayer:
    name: str
    attachment: float      # Deductible / Attachment Point
    limit: float           # Coverage Limit
    rate_on_line: float    # Premium Rate (% of limit)
    
    def ceded_loss(self, gross_loss: float) -> float:
        if gross_loss <= self.attachment:
            return 0.0
        excess = gross_loss - self.attachment
        return min(excess, self.limit)
    
    def premium(self) -> float:
        return self.rate_on_line * self.limit

def apply_reinsurance_structure(df_payouts: pd.DataFrame, layers: List[ReinsuranceLayer]) -> pd.DataFrame:
    """
    Applies multiple reinsurance layers.
    """
    df = df_payouts.copy()
    df['gross'] = df['payout']
    
    for layer in layers:
        col_ceded = f'ceded_{layer.name}'
        df[col_ceded] = df['gross'].apply(layer.ceded_loss)
    
    ceded_cols = [c for c in df.columns if c.startswith('ceded_')]
    df['total_ceded'] = df[ceded_cols].sum(axis=1)
    df['net'] = df['gross'] - df['total_ceded']
    
    return df

def reinsurance_metrics(df_net_structure: pd.DataFrame, layers: List[ReinsuranceLayer]) -> Dict[str, float]:
    aal_gross = df_net_structure['gross'].mean()
    aal_ceded = df_net_structure['total_ceded'].mean()
    aal_net = df_net_structure['net'].mean()
    total_reinsurance_premium = sum(L.premium() for L in layers)

    return {
        "AAL_gross": float(aal_gross),
        "AAL_ceded": float(aal_ceded),
        "AAL_net": float(aal_net),
        "reinsurance_premium": float(total_reinsurance_premium),
        "estimated_net_result": float(aal_ceded - total_reinsurance_premium) 
        # (Ceded Loss - Premium paid) -> checks if reinsurance is efficient or costly
    }

# =========================
# 6. Commercial Pricing
# =========================

def calculate_commercial_rate(
    aal_gross: float,
    sum_insured: float,
    expense_load: float = 0.25,
    profit_margin: float = 0.10,
    capital_cost: float = 0.05,
    var_95: Optional[float] = None,
    risk_adjustment: float = 0.05
) -> Dict[str, float]:
    """
    Calculates Technical and Commercial Rates.
    """
    if sum_insured <= 0:
        return {}

    pure_rate = aal_gross / sum_insured
    
    # Capital cost logic: often % of VaR or Capital Required
    # Here simplified as % of VaR if provided, else just a flat load on Sum Insured? 
    # The user logic was: capital_cost * (var_95 / sum_insured)
    
    capital_rate = 0.0
    if var_95:
        capital_rate = capital_cost * (var_95 / sum_insured)
    else:
        # Fallback if no VaR provided, assume standard capital requirement 
        # e.g. Solvency II is ~1.5 * AAL or similar. Let's stick to user logic.
        capital_rate = capital_cost # Default fallback from user logic seems to be just applying the rate? 
        # actually user code: taxa_capital = custo_capital * (var_95 / soma_segurada) if var_95 else custo_capital
        pass

    technical_rate = pure_rate * (1 + expense_load + capital_rate + risk_adjustment)
    commercial_rate = technical_rate * (1 + profit_margin)
    
    return {
        'pure_rate': pure_rate,
        'expense_load_rate': expense_load,
        'capital_cost_rate': capital_rate,
        'risk_adj_rate': risk_adjustment,
        'technical_rate': technical_rate,
        'profit_margin_rate': profit_margin,
        'commercial_rate': commercial_rate,
        'pure_risk_premium': aal_gross,
        'commercial_premium': commercial_rate * sum_insured
    }
