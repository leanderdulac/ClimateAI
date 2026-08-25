"""Register HTTP routers on the FastAPI application."""

from fastapi import FastAPI

from api.alertas import router as alertas_router
from api.agri_strategy import router as agri_strategy_router
from api.auth import router as auth_router
from api.auth_forgot_password import router as forgot_password_router
from api.audit import router as audit_router
from api.backtesting import router as backtesting_router
from api.bayesian_bootstrap import router as bayesian_bootstrap_router
from api.blockchain_tokens import router as blockchain_tokens_router
from api.cache import router as cache_router
from api.clima import router as clima_router
from api.climate_alert import router as climate_alert_router
from api.climate_capital_charge import router as climate_capital_charge_router
from api.climate_hmm import router as climate_hmm_router
from api.climate_premium import router as climate_premium_router
from api.climate_risk_analysis import router as climate_risk_analysis_router
from api.climate_risk_modeling import router as climate_risk_modeling_router
from api.climate_risk_report import router as climate_risk_report_router
from api.climate_scr import router as climate_scr_router
from api.comprehensive_pricing import router as comprehensive_pricing_router
from api.concentration_risk import router as concentration_risk_router
from api.dynamic_insurance_analysis import router as dynamic_insurance_analysis_router

try:
    from api.dynamical_climate import router as dynamical_climate_router
except ImportError:
    dynamical_climate_router = None

from api.english_api import router as english_api_router
from api.english_climatewise import router as english_climatewise_router
from api.ensemble_pricing import router as ensemble_pricing_router
from api.eventos import router as eventos_router
from api.external import router as external_router
from api.gemini_integration import router as gemini_integration_router
from api.grok_integration import router as grok_integration_router
from api.noaa_integration import router as noaa_integration_router
from api.xweather_forecast import router as xweather_forecast_router
from api.model_governance import router as model_governance_router
from api.regulatory_reporting import router as regulatory_reporting_router
from api.inmet_alertas import router as inmet_alertas_router
from api.brazil_disaster_alerts import router as brazil_disaster_alerts_router
from api.atlas_disasters import router as atlas_disasters_router
from api.atlas_integration import router as atlas_integration_router
from api.atlas_oracle_simulation import router as atlas_oracle_simulation_router
from api.atlas_realtime_climate import router as atlas_realtime_climate_router
from api.unified_platform import router as unified_platform_router
from api.parametric_trigger_verification import router as parametric_trigger_router
from api.i18n import router as i18n_router
from api.news_crawler import router as news_crawler_router
from api.climate_data import router as climate_data_router
from api.ia_analytics_agent import router as ia_analytics_agent_router
from api.integrated_pipeline import router as integrated_pipeline_router
from api.integrated_pricing_framework import (
    router as integrated_pricing_framework_router,
)
from api.investment_return import router as investment_return_router
from api.lei_analysis import router as lei_analysis_router
from api.loading_margin import router as loading_margin_router
from api.localizacao import router as localizacao_router

try:
    from api.lstm_attention import router as lstm_attention_router
except ImportError:
    lstm_attention_router = None

from api.mathematical_engines import router as mathematical_engines_router
from api.microsegmentation import router as microsegmentation_router
from api.mitigation_measures import router as mitigation_measures_router

try:
    from api.ml import router as ml_router
except ImportError:
    ml_router = None

from api.modelagem import router as modelagem_router
from api.operating_costs import router as operating_costs_router
from api.parametric import router as parametric_router
from api.transparency import router as transparency_router
from api.carbon import router as carbon_router
from api.parametric_insurance import router as parametric_insurance_router
from api.performance_testing import router as performance_testing_router
from api.physical_risk import router as physical_risk_router
from api.policy_pricing import router as policy_pricing_router
from api.policy_uncertainty import router as policy_uncertainty_router
from api.policy_valuation import router as policy_valuation_router
from api.policy_risk_monitor import router as policy_risk_monitor_router
from api.probabilistic_climate_scenarios import (
    router as probabilistic_climate_scenarios_router,
)
from api.previsao import router as previsao_router
from api.pricing import router as pricing_router
from api.extreme_value_pricing import router as extreme_value_pricing_router
from api.sips_performance_analytics import router as sips_performance_analytics_router
from api.smart_exclusions import router as smart_exclusions_router
from api.tcfd_issb import router as tcfd_issb_router
from api.tokenizacao import router as tokenizacao_router
from api.transition_risk import router as transition_risk_router
from api.unified_pricing import router as unified_pricing_router
from api.var_backtesting import router as var_backtesting_router
from api.hathor_blockchain import router as hathor_blockchain_router
from api.celestrak import router as celestrak_router
from api.partner import router as partner_router
from api.partners import router as partners_admin_router
from api.logging import get_logger

logger = get_logger()


def register_routers(app: FastAPI, api_prefix: str) -> None:
    """Mount every HTTP router. Fail fast if a required module cannot be included."""
    try:
        app.include_router(clima_router, prefix=f"{api_prefix}/clima", tags=["clima"])
        app.include_router(
            previsao_router, prefix=f"{api_prefix}/previsao", tags=["previsao"]
        )
        app.include_router(
            xweather_forecast_router,
            prefix=f"{api_prefix}/xweather",
            tags=["xweather-forecast"],
        )
        app.include_router(eventos_router, prefix=f"{api_prefix}/eventos", tags=["eventos"])
        app.include_router(
            tokenizacao_router, prefix=f"{api_prefix}/tokenizacao", tags=["tokenizacao"]
        )
        app.include_router(
            blockchain_tokens_router, prefix=f"{api_prefix}/blockchain", tags=["blockchain"]
        )
        app.include_router(
            modelagem_router, prefix=f"{api_prefix}/modelagem", tags=["modelagem"]
        )
        app.include_router(alertas_router, prefix=f"{api_prefix}/alertas", tags=["alertas"])
        app.include_router(
            localizacao_router, prefix=f"{api_prefix}/localizacao", tags=["localizacao"]
        )
        app.include_router(auth_router, prefix=f"{api_prefix}/auth", tags=["auth"])
        app.include_router(forgot_password_router, prefix=f"{api_prefix}/auth", tags=["auth"])
        app.include_router(
            mathematical_engines_router,
            prefix=f"{api_prefix}/math-engines",
            tags=["mathematical-engines"],
        )
        app.include_router(
            climate_risk_modeling_router,
            prefix=f"{api_prefix}/climate-risk",
            tags=["climate-risk-modeling"],
        )
        if lstm_attention_router:
            app.include_router(
                lstm_attention_router,
                prefix=f"{api_prefix}/lstm-attention",
                tags=["lstm-attention"],
            )
        app.include_router(parametric_router, prefix=f"{api_prefix}")
        app.include_router(transparency_router, prefix=f"{api_prefix}")
        app.include_router(carbon_router, prefix=f"{api_prefix}")
        try:
            from api.oracle import router as oracle_router

            app.include_router(oracle_router, prefix=f"{api_prefix}")
        except Exception as exc:
            logger.warning(f"Oracle router not loaded: {exc}")
        app.include_router(
            parametric_insurance_router,
            prefix=f"{api_prefix}/parametric-insurance",
            tags=["parametric-insurance"],
        )
        app.include_router(
            climate_hmm_router, prefix=f"{api_prefix}/climate-hmm", tags=["climate-hmm"]
        )
        app.include_router(
            ensemble_pricing_router,
            prefix=f"{api_prefix}/ensemble-pricing",
            tags=["ensemble-pricing"],
        )
        app.include_router(
            extreme_value_pricing_router,
            prefix=f"{api_prefix}/pricing/extreme-value",
            tags=["extreme-value-pricing"],
        )
        app.include_router(
            climate_risk_analysis_router,
            prefix=f"{api_prefix}/climate-risk-analysis",
            tags=["climate-risk-analysis"],
        )
        app.include_router(
            climate_premium_router,
            prefix=f"{api_prefix}/climate-premium",
            tags=["climate-premium"],
        )
        app.include_router(
            bayesian_bootstrap_router,
            prefix=f"{api_prefix}/bayesian-bootstrap",
            tags=["bayesian-bootstrap"],
        )
        app.include_router(
            climate_alert_router,
            prefix=f"{api_prefix}/climate-alert",
            tags=["climate-alert"],
        )
        app.include_router(
            performance_testing_router,
            prefix=f"{api_prefix}/performance-testing",
            tags=["performance-testing"],
        )
        if dynamical_climate_router:
            app.include_router(
                dynamical_climate_router,
                prefix=f"{api_prefix}/dynamical-climate",
                tags=["dynamical-climate"],
            )
        app.include_router(
            dynamic_insurance_analysis_router,
            prefix=f"{api_prefix}/dynamic-insurance",
            tags=["dynamic-insurance"],
        )
        app.include_router(
            integrated_pipeline_router,
            prefix=f"{api_prefix}/integrated-pipeline",
            tags=["integrated-pipeline"],
        )
        app.include_router(
            physical_risk_router,
            prefix=f"{api_prefix}/physical-risk",
            tags=["physical-risk"],
        )
        app.include_router(
            transition_risk_router,
            prefix=f"{api_prefix}/transition-risk",
            tags=["transition-risk"],
        )
        app.include_router(
            concentration_risk_router,
            prefix=f"{api_prefix}/concentration-risk",
            tags=["concentration-risk"],
        )
        app.include_router(
            mitigation_measures_router,
            prefix=f"{api_prefix}/mitigation-measures",
            tags=["mitigation-measures"],
        )
        app.include_router(
            lei_analysis_router, prefix=f"{api_prefix}/lei-analysis", tags=["lei-analysis"]
        )
        app.include_router(
            operating_costs_router,
            prefix=f"{api_prefix}/operating-costs",
            tags=["operating-costs"],
        )
        app.include_router(
            climate_capital_charge_router,
            prefix=f"{api_prefix}/climate-capital-charge",
            tags=["climate-capital-charge"],
        )
        app.include_router(
            loading_margin_router,
            prefix=f"{api_prefix}/loading-margin",
            tags=["loading-margin"],
        )
        app.include_router(
            investment_return_router,
            prefix=f"{api_prefix}/investment-return",
            tags=["investment-return"],
        )
        app.include_router(
            comprehensive_pricing_router,
            prefix=f"{api_prefix}/comprehensive-pricing",
            tags=["comprehensive-pricing"],
        )
        app.include_router(
            integrated_pricing_framework_router,
            prefix=f"{api_prefix}/integrated-pricing-framework",
            tags=["integrated-pricing-framework"],
        )
        app.include_router(
            climate_risk_report_router,
            prefix=f"{api_prefix}/climate-risk-report",
            tags=["climate-risk-report"],
        )
        app.include_router(
            tcfd_issb_router, prefix=f"{api_prefix}/tcfd-issb", tags=["tcfd-issb"]
        )
        app.include_router(
            climate_scr_router, prefix=f"{api_prefix}/climate-scr", tags=["climate-scr"]
        )
        app.include_router(
            policy_uncertainty_router,
            prefix=f"{api_prefix}/policy-uncertainty",
            tags=["policy-uncertainty"],
        )
        app.include_router(
            smart_exclusions_router,
            prefix=f"{api_prefix}/smart-exclusions",
            tags=["smart-exclusions"],
        )
        app.include_router(
            sips_performance_analytics_router,
            prefix=f"{api_prefix}/sips-analytics",
            tags=["sips-analytics"],
        )
        app.include_router(
            ia_analytics_agent_router, prefix=f"{api_prefix}/ia-agent", tags=["ia-agent"]
        )
        app.include_router(
            gemini_integration_router, prefix=f"{api_prefix}/gemini", tags=["gemini"]
        )
        app.include_router(
            grok_integration_router, prefix=f"{api_prefix}/grok", tags=["grok"]
        )
        app.include_router(
            noaa_integration_router, prefix=f"{api_prefix}/noaa", tags=["noaa"]
        )
        app.include_router(
            model_governance_router,
            prefix=f"{api_prefix}/model-governance",
            tags=["model-governance"],
        )
        app.include_router(
            regulatory_reporting_router,
            prefix=f"{api_prefix}/regulatory-reporting",
            tags=["regulatory-reporting"],
        )
        app.include_router(
            inmet_alertas_router,
            prefix=f"{api_prefix}/inmet-alertas",
            tags=["inmet-alertas"],
        )
        app.include_router(
            brazil_disaster_alerts_router,
            prefix=f"{api_prefix}/brazil-alerts",
            tags=["brazil-alerts"],
        )
        app.include_router(
            atlas_disasters_router, prefix=api_prefix, tags=["atlas-disasters"]
        )
        app.include_router(
            atlas_integration_router, prefix=api_prefix, tags=["atlas-integration"]
        )
        app.include_router(
            atlas_oracle_simulation_router, prefix=api_prefix, tags=["atlas-simulation"]
        )
        app.include_router(
            atlas_realtime_climate_router, prefix=api_prefix, tags=["atlas-realtime"]
        )
        app.include_router(news_crawler_router, prefix=api_prefix, tags=["news-crawler"])
        app.include_router(climate_data_router, prefix=api_prefix, tags=["climate-data"])
        app.include_router(
            unified_platform_router, prefix=api_prefix, tags=["unified-platform"]
        )
        app.include_router(agri_strategy_router, prefix=api_prefix, tags=["agri-strategy"])
        app.include_router(
            var_backtesting_router, prefix=api_prefix, tags=["var-backtesting"]
        )
        app.include_router(
            parametric_trigger_router,
            prefix=f"{api_prefix}/parametric-triggers",
            tags=["parametric-triggers"],
        )
        app.include_router(
            policy_valuation_router,
            prefix=f"{api_prefix}/policy-valuation",
            tags=["policy-valuation"],
        )
        app.include_router(
            policy_pricing_router,
            prefix=f"{api_prefix}/policy-pricing",
            tags=["policy-pricing"],
        )
        app.include_router(
            policy_risk_monitor_router,
            prefix=f"{api_prefix}/risk-monitor",
            tags=["risk-monitor"],
        )
        app.include_router(
            probabilistic_climate_scenarios_router,
            prefix=f"{api_prefix}/probabilistic-climate-scenarios",
            tags=["probabilistic-climate-scenarios"],
        )
        app.include_router(i18n_router, prefix=f"{api_prefix}/i18n", tags=["i18n"])
        app.include_router(
            english_api_router, prefix=f"{api_prefix}/english", tags=["english"]
        )
        app.include_router(
            english_climatewise_router,
            prefix=f"{api_prefix}/english-climatewise",
            tags=["english-climatewise"],
        )
        app.include_router(cache_router, prefix=f"{api_prefix}/cache", tags=["cache"])
        if ml_router:
            app.include_router(ml_router, prefix=f"{api_prefix}/ml", tags=["ml"])
        app.include_router(
            external_router, prefix=f"{api_prefix}/external", tags=["external"]
        )
        app.include_router(
            microsegmentation_router,
            prefix=f"{api_prefix}/microsegmentation",
            tags=["microsegmentation"],
        )
        app.include_router(pricing_router, prefix=f"{api_prefix}/pricing", tags=["pricing"])
        app.include_router(
            unified_pricing_router,
            prefix=f"{api_prefix}/unified-pricing",
            tags=["unified-pricing"],
        )
        app.include_router(backtesting_router, prefix=f"{api_prefix}", tags=["backtesting"])
        app.include_router(
            hathor_blockchain_router,
            prefix=f"{api_prefix}/blockchain/hathor",
            tags=["hathor_blockchain"],
        )
        app.include_router(
            celestrak_router, prefix=f"{api_prefix}/celestrak", tags=["celestrak"]
        )
        app.include_router(audit_router, prefix=f"{api_prefix}/audit", tags=["audit"])
        app.include_router(partner_router, prefix=api_prefix, tags=["Partner API"])
        app.include_router(partners_admin_router, prefix=api_prefix, tags=["Partners"])
    except Exception as exc:
        logger.error(f"Erro ao incluir routers: {exc}")
        raise
