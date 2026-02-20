from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

from services.openmeteo_service import OpenMeteoService
from core.parametric_actuary import (
    RainfallIndexContract,
    compute_historical_payouts,
    expected_loss_and_metrics,
    calculate_ep_curve,
    calculate_var_tvar,
    ReinsuranceLayer,
    apply_reinsurance_structure,
    reinsurance_metrics,
    calculate_commercial_rate
)
from services.gee_service import GoogleEarthEngineService
from services.data_lake_service import BigQueryDataLakeService
from services.vertex_scoring_service import VertexScoringService
from models.rwa import RWAPolicy
from config.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

router = APIRouter(tags=["Parametric Engine"])

# --- Request Models ---

class ReinsuranceLayerModel(BaseModel):
    name: str = "Layer XL"
    attachment: float = 2000000.0
    limit: float = 5000000.0
    rate_on_line: float = 0.25

class ContractParams(BaseModel):
    area_id: str = "custom_area"
    start_date: str = "01-01"  # MM-DD
    end_date: str = "03-31"    # MM-DD
    trigger_mm: float = 100.0
    exhaustion_mm: float = 200.0
    max_payout: float = 1000000.0
    index_type: str = "max_3day" # max_3day, cum_period
    payment_shape: str = "linear" # linear, step
    
class LossYear(BaseModel):
    year: int
    loss_amount: float # or loss_ratio

class SimulationRequest(BaseModel):
    latitude: float
    longitude: float
    contract: ContractParams
    reinsurance_layers: Optional[List[ReinsuranceLayerModel]] = []
    years_back: int = 20
    actual_losses: Optional[List[LossYear]] = [] # For Basis Risk analysis
    include_ep_curve: bool = False
    
# --- Response Models ---

class MetricSet(BaseModel):
    AAL: float
    p_positive: float
    years_used: int
    years_available: int
    data_quality_score: float = 1.0

class RiskMetrics(BaseModel):
    VaR_95: float
    TVaR_95: float
    VaR_99: float
    TVaR_99: float

class PricingResult(BaseModel):
    technical_rate: float
    commercial_rate: float
    commercial_premium: float
    breakdown: Dict[str, float]

class BasisRiskMetrics(BaseModel):
    corr_payout_vs_loss: float
    false_negative_rate: float
    false_positive_rate: float
    n_coordinated_years: int
    warnings: List[str] = []

class SimulationResponse(BaseModel):
    contract_summary: str
    metrics: MetricSet
    risk_metrics: RiskMetrics
    basis_risk: Optional[BasisRiskMetrics] = None
    pricing: PricingResult
    ep_curve: Optional[Dict[str, List[float]]] = None
    payouts_history: List[Dict[str, Any]]
    warnings: List[str] = []

@router.post("/parametric/simulate", response_model=SimulationResponse)
async def simulate_parametric_contract(request: SimulationRequest, db: AsyncSession = Depends(get_db_session)):
    """
    Runs a rigorous backtesting simulation for a parametric contract.
    Enriched with Phase 1 Intelligence Layer and Local Database Persistence.
    """
    try:
        # --- Validation (AC: 400 Bad Request) ---
        if request.contract.trigger_mm >= request.contract.exhaustion_mm:
             raise HTTPException(
                 status_code=400, 
                 detail={"code": "INVALID_THRESHOLD_CONFIG", "message": "Trigger must be strictly less than Exhaustion."}
             )
        
        # 1. Fetch Historical Data (Climate + Satellite + Benchmarks)
        om = OpenMeteoService()
        gee = GoogleEarthEngineService()
        bq = BigQueryDataLakeService()
        vertex = VertexScoringService()

        end_date = datetime.now()
        start_date = end_date.replace(year=end_date.year - request.years_back)
        
        # Concurrent-ish fetches
        clima_data = await om.obter_historico(
            latitude=request.latitude,
            longitude=request.longitude,
            data_inicio=start_date,
            data_fim=end_date,
            variavel="precipitation_sum" 
        )
        
        satellite_metrics = await gee.get_satellite_metrics(
            request.latitude, request.longitude, start_date, end_date
        )
        
        benchmark_data = await bq.get_historical_benchmarks(
            request.latitude, request.longitude, request.years_back
        )

        if not clima_data:
             raise HTTPException(status_code=404, detail="No historical data found for location")

        # Convert to DataFrame
        df_rain = pd.DataFrame([
            {"area_id": request.contract.area_id, "date": c.data, "rain_mm": c.precipitacao}
            for c in clima_data
        ])
        
        # 2. Setup Contract & Compute Payouts
        contract = RainfallIndexContract(
            area_id=request.contract.area_id,
            start_date=request.contract.start_date,
            end_date=request.contract.end_date,
            trigger_mm=request.contract.trigger_mm,
            exhaustion_mm=request.contract.exhaustion_mm,
            max_payout=request.contract.max_payout,
            index_type=request.contract.index_type
        )
        
        unique_years = {c.data.year for c in clima_data}
        years = sorted(list(unique_years))
        df_payouts = compute_historical_payouts(df_rain, contract, years)
        
        # 3. Calculate Actuarial Metrics
        base_metrics = expected_loss_and_metrics(df_payouts)
        var_metrics_95 = calculate_var_tvar(df_payouts, alpha=0.95)
        var_metrics_99 = calculate_var_tvar(df_payouts, alpha=0.99)
        
        # 4. Phase 1 Intelligence: Scoring
        # We use the VertexScoringService to calculate a composite severity score
        payouts_list = df_payouts['payout'].tolist()
        severity_analysis = vertex.calculate_severity_score(
            payouts_list, satellite_metrics, benchmark_data
        )

        # 5. Pricing
        pricing = calculate_commercial_rate(
            aal_gross=base_metrics['AAL'],
            sum_insured=request.contract.max_payout,
            var_95=var_metrics_95['VaR']
        )
        
        # 6. Response Construction
        res = SimulationResponse(
            contract_summary=f"{request.contract.index_type} (Phase 1 AI Powered)",
            metrics=MetricSet(
                AAL=base_metrics['AAL'],
                p_positive=base_metrics['p_positive'],
                years_used=base_metrics['years_used'],
                years_available=len(unique_years),
                data_quality_score=severity_analysis['confidence']
            ),
            risk_metrics=RiskMetrics(
                VaR_95=var_metrics_95['VaR'], TVaR_95=var_metrics_95['TVaR'],
                VaR_99=var_metrics_99['VaR'], TVaR_99=var_metrics_99['TVaR']
            ),
            pricing=PricingResult(
                technical_rate=pricing.get('technical_rate', 0),
                commercial_rate=pricing.get('commercial_rate', 0),
                commercial_premium=pricing.get('commercial_premium', 0),
                breakdown=pricing
            ),
            payouts_history=df_payouts.to_dict(orient='records'),
            warnings=[f"Severity Score: {severity_analysis['score']} / 5.0", f"Sat Source: {satellite_metrics['source']}"]
        )
        
        # 7. Persistence (RWA Audit Layer)
        # Save a local record of this simulation/policy discovery
        try:
            new_policy = RWAPolicy(
                slot=100, # Default Drought
                owner_address="0xTODO_FROM_AUTH", 
                sum_insured=request.contract.max_payout,
                latitude=request.latitude,
                longitude=request.longitude,
                severity_score=severity_analysis['score'],
                status="simulated",
                metadata_json={
                    "ndvi": satellite_metrics['ndvi'],
                    "soil_moisture": satellite_metrics['soil_moisture'],
                    "source": satellite_metrics['source']
                }
            )
            db.add(new_policy)
            await db.commit()
            logger.info(f"Local RWA policy record saved for ({request.latitude}, {request.longitude})")
        except Exception as e:
            logger.warning(f"Failed to persist local policy record: {e}")

        if request.include_ep_curve:
            ep_curve_df = calculate_ep_curve(df_payouts)
            res.ep_curve = {
                "prob_exceedance": ep_curve_df['prob_exceedance'].tolist(),
                "loss": ep_curve_df['OCC_EP'].tolist()
            }
            
        return res

    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# --- Optimization Models ---

class OptimizationConstraints(BaseModel):
    min_aal: float = 0.0
    max_aal: float = 0.5 # 50%
    target_payout_frequency: Optional[float] = None

class OptimizationRequest(BaseModel):
    latitude: float
    longitude: float
    years_back: int = 20
    constraints: OptimizationConstraints
    actual_losses: Optional[List[LossYear]] = []
    
    # Grid Search Config
    trigger_min: float = 50.0
    trigger_max: float = 200.0
    trigger_step: float = 10.0
    exhaustion_add_min: float = 50.0 # Min gap
    exhaustion_add_max: float = 300.0
    exhaustion_add_step: float = 25.0

class OptimizationResultItem(BaseModel):
    trigger_mm: float
    exhaustion_mm: float
    aal: float
    false_negative_rate: float
    false_positive_rate: float
    correlation: float
    payout_frequency: float

@router.post("/parametric/optimize", response_model=List[OptimizationResultItem])
async def optimize_parametric_contract(request: OptimizationRequest):
    """
    Finds optimal Trigger/Exhaustion pairs using Grid Search.
    Objective: Minimize False Negative Rate subject to AAL constraints.
    """
    try:
        # 1. Fetch Data (Common)
        om = OpenMeteoService()
        end_date = datetime.now()
        start_date = end_date.replace(year=end_date.year - request.years_back)
        
        try:
            clima_data = await om.obter_historico(
                latitude=request.latitude,
                longitude=request.longitude,
                data_inicio=start_date,
                data_fim=end_date,
                variavel="precipitation_sum" 
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to fetch climate data: {str(e)}")
            
        if not clima_data or len(clima_data) < 365*5:
             raise HTTPException(status_code=422, detail="Insufficient climate data due to history depth")

        # Convert
        df_rain = pd.DataFrame([
            {
                "area_id": "opt_area",
                "date": c.data,
                "rain_mm": c.precipitacao
            }
            for c in clima_data
        ])
        
        # 2. Setup Optimizer
        from core.parametric_optimizer import ParametricOptimizer
        optimizer = ParametricOptimizer(df_rain, "opt_area")
        
        # 3. Base Contract Template (Assume max3day and linear for now, could be parametrized)
        base_contract = RainfallIndexContract(
            area_id="opt_area",
            start_date="01-01", # Default full year or parametrized? Let's assume full year MVP
            end_date="12-31",
            trigger_mm=0, # placeholder
            exhaustion_mm=0, # placeholder
            max_payout=1.0, # normalized AAL
            index_type="max_3day"
        )
        
        # 4. Prepare Actual Losses
        df_losses = None
        if request.actual_losses:
            df_losses = pd.DataFrame([l.dict() for l in request.actual_losses])
            df_losses.rename(columns={"loss_amount": "actual_loss_ratio"}, inplace=True)

        # 5. Run Grid Search
        results = optimizer.optimize_grid(
            base_contract=base_contract,
            target_aal_min=request.constraints.min_aal,
            target_aal_max=request.constraints.max_aal,
            df_actual_losses=df_losses,
            trigger_range=(request.trigger_min, request.trigger_max, request.trigger_step),
            exhaustion_add_range=(request.exhaustion_add_min, request.exhaustion_add_max, request.exhaustion_add_step)
        )
        
        # 6. Convert to Response (Top 20 candidates)
        return [
            OptimizationResultItem(
                trigger_mm=r.trigger_mm,
                exhaustion_mm=r.exhaustion_mm,
                aal=r.aal,
                false_negative_rate=r.false_negative_rate,
                false_positive_rate=r.false_positive_rate,
                correlation=r.correlation,
                payout_frequency=r.payout_frequency
            )
            for r in results[:20]
        ]

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
