"""
Climate Services Subpackage
Contains all climate-related services including forecasting, alerts, and risk modeling.
"""

import logging

logger = logging.getLogger(__name__)

from services.clima_service import ClimaService
from services.climate_alert_service import ClimateAlertService
from services.climate_capital_charge_service import ClimateCapitalChargeService
from services.climate_derivative_pricer import ClimateDerivativePricer
from services.climate_hmm_service import ClimateHMMService
from services.climate_premium_service import ClimatePremiumService
from services.climate_risk_modeling_service import ClimateRiskModelingService
from services.climate_risk_report_service import ClimateRiskReportService
from services.climate_scr_service import ClimateSCRService
from services.climate_systemic_risk_service import ClimateSystemicRiskService

try:
    from services.dynamical_climate_service import DynamicalClimateService
except ImportError as e:
    logger.warning(f"DynamicalClimateService unavailable (pynamicalsys not installed): {e}")
    DynamicalClimateService = None

__all__ = [
    "ClimaService",
    "ClimateAlertService",
    "ClimateHMMService",
    "ClimatePremiumService",
    "ClimateRiskModelingService",
    "ClimateRiskReportService",
    "ClimateSCRService",
    "ClimateSystemicRiskService",
    "ClimateCapitalChargeService",
    "ClimateDerivativePricer",
    "DynamicalClimateService",
]
