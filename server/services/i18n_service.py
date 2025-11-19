"""
Internationalization (i18n) Service for ClimateAI
Provides language translations and localization for English and Portuguese
"""

import json
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional  # Add List import


class Language(Enum):
    PT_BR = "pt-BR"
    EN_US = "en-US"


class I18nService:
    """
    Internationalization service providing translations between Portuguese and English
    """

    def __init__(self):
        # Translation dictionaries for key terms
        self.translations = {
            Language.PT_BR: {
                # Climate risk terms
                "climate_risk_score": "Pontuação de Risco Climático",
                "climate_var": "VaR Climático",
                "physical_risk": "Risco Físico",
                "transition_risk": "Risco de Transição",
                "concentration_risk": "Risco de Concentração",
                "mitigation_effectiveness": "Efetividade de Mitigação",
                "model_confidence": "Confiança no Modelo",
                # Financial terms
                "premium": "Prêmio",
                "claims": "Sinistros",
                "expected_loss": "Perda Esperada",
                "profit_margin": "Margem de Lucro",
                "climate_loading": "Carregamento Climático",
                "uncertainty_loading": "Carregamento de Incerteza",
                # Policy terms
                "policy_valuation": "Avaliação de Apólice",
                "valuation_score": "Pontuação de Avaliação",
                "valuation_tier": "Nível de Avaliação",
                "excellent": "Excelente",
                "good": "Bom",
                "fair": "Razoável",
                "poor": "Ruim",
                "avoid": "Evitar",
                # System terms
                "system_performance": "Desempenho do Sistema",
                "risk_assessment": "Avaliação de Risco",
                "premium_calculation": "Cálculo de Prêmio",
                "claim_assessment": "Avaliação de Sinistro",
                # TCFD/ISSB terms
                "tcfd_reporting": "Relatórios TCFD",
                "issb_compliance": "Conformidade ISSB",
                "climate_disclosures": "Divulgações Climáticas",
                "physical_risk_metric": "Métrica de Risco Físico",
                "transition_risk_metric": "Métrica de Risco de Transição",
                "stress_scenario": "Cenário de Estresse",
                "mitigation_efforts": "Esforços de Mitigação",
                # Notifications
                "notification": "Notificação",
                "alert": "Alerta",
                "warning": "Aviso",
                "emergency": "Emergência",
                "high_risk": "Alto Risco",
                "medium_risk": "Risco Médio",
                "low_risk": "Baixo Risco",
                # Geographic
                "geographic_risk": "Risco Geográfico",
                "microsegmentation": "Microsegmentação",
                "location_analysis": "Análise de Localização",
                # Messages
                "service_operational": "Serviço operacional",
                "calculation_successful": "Cálculo realizado com sucesso",
                "data_received": "Dados recebidos",
                "analysis_complete": "Análise completa",
                "system_ready": "Sistema pronto",
                "processing_complete": "Processamento completo",
                # Error messages
                "invalid_input": "Entrada inválida",
                "calculation_error": "Erro no cálculo",
                "data_not_found": "Dados não encontrados",
                "api_error": "Erro na API",
                "insufficient_data": "Dados insuficientes",
                "service_unavailable": "Serviço indisponível",
                "permission_denied": "Permissão negada",
                # Climate events
                "flood": "Inundação",
                "drought": "Seca",
                "extreme_heat": "Onda de Calor",
                "hail": "Granizo",
                "wind_storm": "Tempestade de Vento",
                "wildfire": "Incêndio Florestal",
                # Mitigation measures
                "flood_defenses": "Defesas contra Inundações",
                "drainage_systems": "Sistemas de Drenagem",
                "resistant_construction": "Construção Resistente",
                "early_warning": "Sistema de Alerta Precoce",
                "vegetation_barriers": "Barreiras de Vegetação",
                # Premium components
                "base_premium": "Prêmio Base",
                "risk_loading": "Carregamento de Risco",
                "profit_loading": "Carregamento de Lucro",
                "expense_loading": "Carregamento de Despesas",
                "contingency_loading": "Carregamento de Contingência",
                "catastrophe_loading": "Carregamento de Catástrofe",
                # Claims components
                "validated_claims": "Sinistros Validados",
                "pending_claims": "Sinistros Pendentes",
                "rejected_claims": "Sinistros Rejeitados",
                "fraudulent_claims": "Sinistros Fraudulentos",
                "settlement_amount": "Valor de Liquidação",
                "adjustment_factor": "Fator de Ajuste",
                # Technical terms
                "value_at_risk": "Valor em Risco",
                "expected_shortfall": "Perda Esperada Condicioal",
                "probability_analysis": "Análise de Probabilidade",
                "correlation_matrix": "Matriz de Correlação",
                "monte_carlo": "Simulação Monte Carlo",
                "bayesian_analysis": "Análise Bayesiana",
                # API responses
                "status": "Status",
                "success": "Sucesso",
                "failed": "Falhou",
                "timestamp": "Timestamp",
                "request_id": "ID da Requisição",
                "result": "Resultado",
                "details": "Detalhes",
                # TCFD/ISSB reporting metrics
                "var_1year_climatico": "VaR_1ano_climático",
                "carbon_tax_exposure": "Exposição CarbonTax",
                "rcp_85_loss": "Perda em RCP 8.5",
                "resilience_score": "Score de resiliência",
                "climate_scenario_risk": "Risco do Cenário Climático",
                "transition_risk_exposure": "Exposição de Risco de Transição",
                "physical_risk_exposure": "Exposição de Risco Físico",
                # Risk categories
                "climate_risk": "Risco Climático",
                "weather_risk": "Risco Climático",
                "catastrophic_risk": "Risco Catastrófico",
                "systematic_risk": "Risco Sistemático",
                "idiosyncratic_risk": "Risco Idiossincrático",
                "model_risk": "Risco de Modelo",
                "data_quality_risk": "Risco de Qualidade de Dados",
                # System metrics
                "system_efficiency": "Eficiência do Sistema",
                "prediction_accuracy": "Acurácia de Predição",
                "processing_speed": "Velocidade de Processamento",
                "data_integration": "Integração de Dados",
                "model_performance": "Desempenho do Modelo",
                "user_satisfaction": "Satisfação do Usuário",
                # General terms
                "climate_ai_system": "Sistema ClimateAI",
                "climate_analytics": "Análise Climática",
                "risk_modelling": "Modelagem de Risco",
                "insurance_pricing": "Precificação de Seguros",
                "climate_resilience": "Resiliência Climática",
                "sustainability_metrics": "Métricas de Sustentabilidade",
                # Climate indices
                "spi": "Índice de Precipitação Padronizado (SPI)",
                "rwi": "Índice de Umidade Relativa (RWI)",
                "spei": "Índice de Precipitação e Evapotranspiração Padronizado (SPEI)",
                "pdsi": "Índice de Severe de Palmer (PDSI)",
                # Data sources
                "embrapa_api": "API da Embrapa",
                "openmeteo_api": "API OpenMeteo",
                "cmip_data": "Dados CMIP",
                "historical_data": "Dados Históricos",
                "real_time_data": "Dados em Tempo Real",
                # Service descriptions
                "tcfd_issb_service": "Serviço de Relatórios TCFD/ISSB",
                "climate_scr_service": "Serviço de SCR Climático",
                "policy_valuation_service": "Serviço de Avaliação de Apólices",
                "smart_exclusions_service": "Serviço de Exclusões Inteligentes",
                "sips_analytics_service": "Serviço de Análise SIPS-Climate",
            },
            Language.EN_US: {
                # Climate risk terms
                "climate_risk_score": "Climate Risk Score",
                "climate_var": "Climate VaR",
                "physical_risk": "Physical Risk",
                "transition_risk": "Transition Risk",
                "concentration_risk": "Concentration Risk",
                "mitigation_effectiveness": "Mitigation Effectiveness",
                "model_confidence": "Model Confidence",
                # Financial terms
                "premium": "Premium",
                "claims": "Claims",
                "expected_loss": "Expected Loss",
                "profit_margin": "Profit Margin",
                "climate_loading": "Climate Loading",
                "uncertainty_loading": "Uncertainty Loading",
                # Policy terms
                "policy_valuation": "Policy Valuation",
                "valuation_score": "Valuation Score",
                "valuation_tier": "Valuation Tier",
                "excellent": "Excellent",
                "good": "Good",
                "fair": "Fair",
                "poor": "Poor",
                "avoid": "Avoid",
                # System terms
                "system_performance": "System Performance",
                "risk_assessment": "Risk Assessment",
                "premium_calculation": "Premium Calculation",
                "claim_assessment": "Claim Assessment",
                # TCFD/ISSB terms
                "tcfd_reporting": "TCFD Reporting",
                "issb_compliance": "ISSB Compliance",
                "climate_disclosures": "Climate Disclosures",
                "physical_risk_metric": "Physical Risk Metric",
                "transition_risk_metric": "Transition Risk Metric",
                "stress_scenario": "Stress Scenario",
                "mitigation_efforts": "Mitigation Efforts",
                # Notifications
                "notification": "Notification",
                "alert": "Alert",
                "warning": "Warning",
                "emergency": "Emergency",
                "high_risk": "High Risk",
                "medium_risk": "Medium Risk",
                "low_risk": "Low Risk",
                # Geographic
                "geographic_risk": "Geographic Risk",
                "microsegmentation": "Microsegmentation",
                "location_analysis": "Location Analysis",
                # Messages
                "service_operational": "Service operational",
                "calculation_successful": "Calculation successful",
                "data_received": "Data received",
                "analysis_complete": "Analysis complete",
                "system_ready": "System ready",
                "processing_complete": "Processing complete",
                # Error messages
                "invalid_input": "Invalid input",
                "calculation_error": "Calculation error",
                "data_not_found": "Data not found",
                "api_error": "API error",
                "insufficient_data": "Insufficient data",
                "service_unavailable": "Service unavailable",
                "permission_denied": "Permission denied",
                # Climate events
                "flood": "Flood",
                "drought": "Drought",
                "extreme_heat": "Heat Wave",
                "hail": "Hail",
                "wind_storm": "Wind Storm",
                "wildfire": "Wildfire",
                # Mitigation measures
                "flood_defenses": "Flood Defenses",
                "drainage_systems": "Drainage Systems",
                "resistant_construction": "Resistant Construction",
                "early_warning": "Early Warning System",
                "vegetation_barriers": "Vegetation Barriers",
                # Premium components
                "base_premium": "Base Premium",
                "risk_loading": "Risk Loading",
                "profit_loading": "Profit Loading",
                "expense_loading": "Expense Loading",
                "contingency_loading": "Contingency Loading",
                "catastrophe_loading": "Catastrophe Loading",
                # Claims components
                "validated_claims": "Validated Claims",
                "pending_claims": "Pending Claims",
                "rejected_claims": "Rejected Claims",
                "fraudulent_claims": "Fraudulent Claims",
                "settlement_amount": "Settlement Amount",
                "adjustment_factor": "Adjustment Factor",
                # Technical terms
                "value_at_risk": "Value at Risk",
                "expected_shortfall": "Expected Shortfall",
                "probability_analysis": "Probability Analysis",
                "correlation_matrix": "Correlation Matrix",
                "monte_carlo": "Monte Carlo Simulation",
                "bayesian_analysis": "Bayesian Analysis",
                # API responses
                "status": "Status",
                "success": "Success",
                "failed": "Failed",
                "timestamp": "Timestamp",
                "request_id": "Request ID",
                "result": "Result",
                "details": "Details",
                # TCFD/ISSB reporting metrics
                "var_1year_climatico": "Var_1year_climatico",
                "carbon_tax_exposure": "Carbon Tax Exposure",
                "rcp_85_loss": "RCP 8.5 Loss",
                "resilience_score": "Resilience Score",
                "climate_scenario_risk": "Climate Scenario Risk",
                "transition_risk_exposure": "Transition Risk Exposure",
                "physical_risk_exposure": "Physical Risk Exposure",
                # Risk categories
                "climate_risk": "Climate Risk",
                "weather_risk": "Weather Risk",
                "catastrophic_risk": "Catastrophic Risk",
                "systematic_risk": "Systematic Risk",
                "idiosyncratic_risk": "Idiosyncratic Risk",
                "model_risk": "Model Risk",
                "data_quality_risk": "Data Quality Risk",
                # System metrics
                "system_efficiency": "System Efficiency",
                "prediction_accuracy": "Prediction Accuracy",
                "processing_speed": "Processing Speed",
                "data_integration": "Data Integration",
                "model_performance": "Model Performance",
                "user_satisfaction": "User Satisfaction",
                # General terms
                "climate_ai_system": "ClimateAI System",
                "climate_analytics": "Climate Analytics",
                "risk_modelling": "Risk Modelling",
                "insurance_pricing": "Insurance Pricing",
                "climate_resilience": "Climate Resilience",
                "sustainability_metrics": "Sustainability Metrics",
                # Climate indices
                "spi": "Standardized Precipitation Index (SPI)",
                "rwi": "Relative Wetness Index (RWI)",
                "spei": "Standardized Precipitation Evapotranspiration Index (SPEI)",
                "pdsi": "Palmer Drought Severity Index (PDSI)",
                # Data sources
                "embrapa_api": "Embrapa API",
                "openmeteo_api": "OpenMeteo API",
                "cmip_data": "CMIP Data",
                "historical_data": "Historical Data",
                "real_time_data": "Real-time Data",
                # Service descriptions
                "tcfd_issb_service": "TCFD/ISSB Reporting Service",
                "climate_scr_service": "Climate SCR Service",
                "policy_valuation_service": "Policy Valuation Service",
                "smart_exclusions_service": "Smart Exclusions Service",
                "sips_analytics_service": "SIPS-Climate Analytics Service",
            },
        }

    def translate(self, key: str, language: Language = Language.EN_US) -> str:
        """
        Translate a key to the specified language

        Args:
            key: The term to translate
            language: Target language (default EN_US)

        Returns:
            Translated term or original key if not found
        """
        if language in self.translations and key in self.translations[language]:
            return self.translations[language][key]
        else:
            # Return the key as is if translation not found
            return key

    def get_translations_for_language(self, language: Language) -> Dict[str, str]:
        """
        Get all translations for a specific language

        Args:
            language: Target language

        Returns:
            Dictionary of all translations for that language
        """
        return self.translations.get(language, {})

    def get_available_languages(self) -> List[str]:
        """
        Get list of available languages

        Returns:
            List of available language codes
        """
        return [lang.value for lang in Language]


# Global instance
i18n_service = I18nService()


def translate_term(key: str, language: str = "en-US") -> str:
    """Convenience function to translate a term"""
    lang_enum = Language.EN_US if language == "en-US" else Language.PT_BR
    return i18n_service.translate(key, lang_enum)


def get_translations(lang_code: str = "en-US") -> Dict[str, str]:
    """Convenience function to get translations for a language"""
    lang_enum = Language.EN_US if lang_code == "en-US" else Language.PT_BR
    return i18n_service.get_translations_for_language(lang_enum)


def get_available_languages() -> List[str]:
    """Convenience function to get available languages"""
    return i18n_service.get_available_languages()
