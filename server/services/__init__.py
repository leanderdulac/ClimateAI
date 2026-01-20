"""
Services Package
Organized into thematic subpackages for better maintainability.

Subpackages:
- climate: Climate-related services (forecasting, alerts, risk modeling)
- risk: Risk analysis and assessment services
- pricing: Actuarial and pricing services
- external: External API integrations
- ai: Machine learning and AI services
- modules: Regulatory and calculation modules
- core: Core business services
"""

# Subpackage imports (for convenience)
from services import ai, climate, core, external, modules, pricing, risk

# Re-export commonly used services for backwards compatibility
from services.audit_service import (
    get_audit_logs,
    get_compliance_report,
    log_operation,
    log_policy_decision,
    log_risk_assessment,
)
from services.external_api_service import (
    get_commodity_prices,
    get_economic_indicators,
    get_real_time_data,
    get_weather_data,
)
from services.microsegmentation_service import (
    analyze_location_risk,
    create_microsegments,
    get_microsegmentation_summary,
)
from services.ml_service import get_ml_model_info, predict_sinistrality, train_ml_models

__all__ = [
    # Audit functions
    "log_operation",
    "log_policy_decision",
    "log_risk_assessment",
    "get_audit_logs",
    "get_compliance_report",
    # ML functions
    "predict_sinistrality",
    "train_ml_models",
    "get_ml_model_info",
    # External API functions
    "get_weather_data",
    "get_economic_indicators",
    "get_commodity_prices",
    "get_real_time_data",
    # Microsegmentation functions
    "create_microsegments",
    "analyze_location_risk",
    "get_microsegmentation_summary",
    # Subpackages
    "climate",
    "risk",
    "pricing",
    "external",
    "ai",
    "modules",
    "core",
]
