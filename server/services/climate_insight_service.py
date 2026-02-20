"""
Service for analyzing historical climate data to provide insights and extreme event risks
"""

import logging
from typing import Dict, List, Optional
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class ClimateInsightService:
    """
    Analyzes historical climate data to identify predominant patterns 
    and extreme weather event risks.
    """

    def analyze_location_insights(self, climate_data: List[Dict]) -> Dict:
        """
        Analyzes historical data to return climate insights.
        """
        if not climate_data:
            return {
                "predominant_climate": "Dados insuficientes",
                "risk_level": "Desconhecido",
                "extreme_events": [],
                "insight_text": "Não há dados históricos suficientes para esta localização."
            }

        # Extract series
        temps = [d.get("temperature", 0) for d in climate_data if d.get("temperature") is not None]
        precips = [d.get("precipitation", 0) for d in climate_data if d.get("precipitation") is not None]
        
        if not temps or not precips:
            return {
                "predominant_climate": "Dados incompletos",
                "risk_level": "Desconhecido",
                "extreme_events": [],
                "insight_text": "Dados históricos incompletos para processamento estatístico."
            }

        # Calculate statistics
        avg_temp = np.mean(temps)
        total_precip = np.sum(precips)
        days_covered = len(climate_data)
        annual_precip_est = total_precip * (365 / days_covered) if days_covered > 0 else 0

        # 1. Identify Predominant Climate (Simplified Köppen-like logic for Brazil/General)
        climate_type = self._identify_climate_type(avg_temp, annual_precip_est, precips)

        # 2. Analyze Extreme Event Risks
        extreme_risks = self._analyze_extreme_risks(temps, precips)

        # 3. Determine Overall Risk Level
        risk_score = len(extreme_risks)
        if risk_score >= 3:
            risk_level = "Crítico"
        elif risk_score >= 1:
            risk_level = "Moderado"
        else:
            risk_level = "Baixo"

        # 4. Generate Insight Text
        insight_text = self._generate_insight_text(climate_type, extreme_risks, avg_temp)

        return {
            "predominant_climate": climate_type,
            "risk_level": risk_level,
            "extreme_events": extreme_risks,
            "insight_text": insight_text,
            "stats": {
                "avg_temp": round(float(avg_temp), 1),
                "annual_precip_est": round(float(annual_precip_est), 1),
                "max_temp": round(float(np.max(temps)), 1),
                "min_temp": round(float(np.min(temps)), 1)
            }
        }

    def _identify_climate_type(self, avg_temp: float, annual_precip: float, precips: List[float]) -> str:
        """Identify climate type based on temp and precip patterns."""
        if avg_temp > 24 and annual_precip > 1500:
            return "Equatorial / Tropical Úmido"
        elif avg_temp > 20 and annual_precip < 800:
            return "Semiárido"
        elif avg_temp < 18:
            return "Subtropical"
        elif 18 <= avg_temp <= 24:
            # Check for seasonality
            std_precip = np.std(precips)
            if std_precip > 50:
                return "Tropical de Altitude / Sazonal"
            return "Tropical"
        return "Temperado / Tropical"

    def _analyze_extreme_risks(self, temps: List[float], precips: List[float]) -> List[Dict]:
        """Check for specific extreme event thresholds."""
        risks = []

        # Heatwaves (Extreme Heat)
        heat_days = len([t for t in temps if t > 38])
        if heat_days > 5:
            risks.append({
                "type": "Onda de Calor",
                "severity": "Alta" if heat_days > 15 else "Média",
                "description": f"Histórico de {heat_days} dias com temperaturas acima de 38°C.",
                "icon": "SunMedium"
            })

        # Frost (Extreme Cold)
        frost_days = len([t for t in temps if t < 4])
        if frost_days > 2:
            risks.append({
                "type": "Geada",
                "severity": "Alta" if frost_days > 10 else "Média",
                "description": f"Registrados {frost_days} dias com potencial de geada.",
                "icon": "Snowflake"
            })

        # Flooding / Heavy Rain
        heavy_rain_days = len([p for p in precips if p > 50])
        if heavy_rain_days > 3:
            risks.append({
                "type": "Alagamentos / Enxurradas",
                "severity": "Alta" if heavy_rain_days > 8 else "Média",
                "description": f"Frequência elevada de chuvas torrenciais (>50mm/dia).",
                "icon": "CloudRain"
            })

        # Drought (Simplified anomaly check)
        avg_monthly_precip = np.mean(precips) * 30
        if avg_monthly_precip < 50:
            risks.append({
                "type": "Estiagem Prolongada",
                "severity": "Alta" if avg_monthly_precip < 30 else "Média",
                "description": "Precipitação média mensal criticamente baixa.",
                "icon": "Droplets"
            })

        return risks

    def _generate_insight_text(self, climate_type: str, risks: List[Dict], avg_temp: float) -> str:
        """Construct a natural language insight."""
        if not risks:
            return f"Esta região possui um clima {climate_type} estável. É uma área com baixo histórico de eventos extremos severos, sendo ideal para culturas que exigem previsibilidade térmica."
        
        main_risk = risks[0]["type"]
        return f"A região é caracterizada por um clima {climate_type}. O histórico aponta o risco de {main_risk.lower()} como um dos principais fatores limitantes, exigindo estratégias de mitigação e monitoramento constante."

climate_insight_service = ClimateInsightService()
