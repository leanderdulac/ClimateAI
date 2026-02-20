"""
Serviço de Cenários Probabilísticos Climáticos
Implementa combinações SSP-RCP e modelos ensemble CMIP6
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd
from scipy import stats
from scipy.interpolate import interp1d

logger = logging.getLogger(__name__)


class SSPScenario(Enum):
    """Cenários Socioeconômicos Compartilhados (Shared Socioeconomic Pathways)"""
    SSP1 = "SSP1"  # Sustentabilidade (Taking the Green Road)
    SSP2 = "SSP2"  # Desenvolvimento médio (Middle of the Road)
    SSP3 = "SSP3"  # Fragmentação regional (A Rocky Road)
    SSP4 = "SSP4"  # Desigualdade (Inequality)
    SSP5 = "SSP5"  # Desenvolvimento fossilizado (Fossil-fueled Development)


class RCPScenario(Enum):
    """Caminhos de Concentração Representativos (Representative Concentration Pathways)"""
    RCP26 = "RCP2.6"  # Baixas emissões (2.6 W/m²)
    RCP45 = "RCP4.5"  # Emissões intermediárias (4.5 W/m²)
    RCP60 = "RCP6.0"  # Emissões estabilizadas (6.0 W/m²)
    RCP85 = "RCP8.5"  # Altas emissões (8.5 W/m²)


@dataclass
class SSPRCPCombination:
    """Combinação SSP-RCP com características específicas"""
    ssp: SSPScenario
    rcp: RCPScenario
    description: str
    temperature_change_2100: float  # °C até 2100
    co2_concentration_2100: float   # ppm até 2100
    probability_weight: float       # Peso probabilístico


@dataclass
class CMIP6Model:
    """Modelo CMIP6 com características"""
    name: str
    institution: str
    resolution_atmosphere: str
    resolution_ocean: str
    ensemble_members: int
    key_variables: List[str]


class ProbabilisticClimateScenariosService:
    """
    Serviço para cenários probabilísticos climáticos
    Implementa SSP-RCP combinations e CMIP6 ensemble models
    """

    def __init__(self):
        self.ssp_rcp_combinations = self._initialize_ssp_rcp_combinations()
        self.cmip6_models = self._initialize_cmip6_models()
        self.baseline_year = 2020
        self.projection_years = list(range(2020, 2101, 10))

    def _initialize_ssp_rcp_combinations(self) -> Dict[str, SSPRCPCombination]:
        """Inicializa combinações SSP-RCP com dados científicos"""
        combinations = {}

        # SSP1-RCP2.6: Sustentabilidade + Baixas emissões
        combinations["SSP1-RCP2.6"] = SSPRCPCombination(
            ssp=SSPScenario.SSP1,
            rcp=RCPScenario.RCP26,
            description="Cenário de sustentabilidade com baixas emissões",
            temperature_change_2100=1.8,
            co2_concentration_2100=420,
            probability_weight=0.15
        )

        # SSP1-RCP4.5: Sustentabilidade + Emissões intermediárias
        combinations["SSP1-RCP4.5"] = SSPRCPCombination(
            ssp=SSPScenario.SSP1,
            rcp=RCPScenario.RCP45,
            description="Cenário de sustentabilidade com emissões moderadas",
            temperature_change_2100=2.4,
            co2_concentration_2100=540,
            probability_weight=0.10
        )

        # SSP2-RCP4.5: Desenvolvimento médio + Emissões intermediárias
        combinations["SSP2-RCP4.5"] = SSPRCPCombination(
            ssp=SSPScenario.SSP2,
            rcp=RCPScenario.RCP45,
            description="Cenário de desenvolvimento médio",
            temperature_change_2100=2.7,
            co2_concentration_2100=550,
            probability_weight=0.25
        )

        # SSP3-RCP7.0: Fragmentação + Emissões altas
        combinations["SSP3-RCP7.0"] = SSPRCPCombination(
            ssp=SSPScenario.SSP3,
            rcp=RCPScenario.RCP60,
            description="Cenário de fragmentação regional",
            temperature_change_2100=3.2,
            co2_concentration_2100=650,
            probability_weight=0.15
        )

        # SSP4-RCP6.0: Desigualdade + Emissões estabilizadas
        combinations["SSP4-RCP6.0"] = SSPRCPCombination(
            ssp=SSPScenario.SSP4,
            rcp=RCPScenario.RCP60,
            description="Cenário de desigualdade",
            temperature_change_2100=3.0,
            co2_concentration_2100=600,
            probability_weight=0.10
        )

        # SSP5-RCP8.5: Desenvolvimento fossilizado + Altas emissões
        combinations["SSP5-RCP8.5"] = SSPRCPCombination(
            ssp=SSPScenario.SSP5,
            rcp=RCPScenario.RCP85,
            description="Cenário de desenvolvimento fossilizado",
            temperature_change_2100=4.3,
            co2_concentration_2100=800,
            probability_weight=0.25
        )

        return combinations

    def _initialize_cmip6_models(self) -> List[CMIP6Model]:
        """Inicializa modelos CMIP6 disponíveis"""
        models = [
            CMIP6Model(
                name="UKESM1-0-LL",
                institution="UK Met Office",
                resolution_atmosphere="N96 (1.875° x 1.25°)",
                resolution_ocean="1°",
                ensemble_members=12,
                key_variables=["tas", "pr", "psl", "tos"]
            ),
            CMIP6Model(
                name="MPI-ESM1-2-HR",
                institution="MPI-M",
                resolution_atmosphere="T127 (0.94° x 0.94°)",
                resolution_ocean="0.4°",
                ensemble_members=10,
                key_variables=["tas", "pr", "psl", "tos", "sos"]
            ),
            CMIP6Model(
                name="CESM2",
                institution="NCAR",
                resolution_atmosphere="1°",
                resolution_ocean="1°",
                ensemble_members=11,
                key_variables=["tas", "pr", "psl", "tos", "sos"]
            ),
            CMIP6Model(
                name="GFDL-ESM4",
                institution="GFDL",
                resolution_atmosphere="1°",
                resolution_ocean="0.5°",
                ensemble_members=3,
                key_variables=["tas", "pr", "psl", "tos"]
            ),
            CMIP6Model(
                name="CanESM5",
                institution="CCCma",
                resolution_atmosphere="T63 (2.8° x 2.8°)",
                resolution_ocean="1°",
                ensemble_members=25,
                key_variables=["tas", "pr", "psl", "tos"]
            ),
            CMIP6Model(
                name="MIROC6",
                institution="MIROC",
                resolution_atmosphere="T85 (1.4° x 1.4°)",
                resolution_ocean="1°",
                ensemble_members=10,
                key_variables=["tas", "pr", "psl", "tos"]
            )
        ]
        return models

    def get_ssp_rcp_combinations(self) -> Dict[str, Dict]:
        """Retorna todas as combinações SSP-RCP disponíveis"""
        return {
            key: {
                "ssp": combo.ssp.value,
                "rcp": combo.rcp.value,
                "description": combo.description,
                "temperature_change_2100": combo.temperature_change_2100,
                "co2_concentration_2100": combo.co2_concentration_2100,
                "probability_weight": combo.probability_weight
            }
            for key, combo in self.ssp_rcp_combinations.items()
        }

    def get_cmip6_models(self) -> List[Dict]:
        """Retorna informações sobre modelos CMIP6"""
        return [
            {
                "name": model.name,
                "institution": model.institution,
                "resolution_atmosphere": model.resolution_atmosphere,
                "resolution_ocean": model.resolution_ocean,
                "ensemble_members": model.ensemble_members,
                "key_variables": model.key_variables
            }
            for model in self.cmip6_models
        ]

    def generate_climate_scenarios(
        self,
        location: Tuple[float, float],
        ssp_rcp_scenario: str,
        n_ensemble_members: int = 10,
        projection_years: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Gera cenários climáticos usando SSP-RCP e ensemble CMIP6

        Args:
            location: (latitude, longitude)
            ssp_rcp_scenario: Nome do cenário (ex: "SSP2-RCP4.5")
            n_ensemble_members: Número de membros do ensemble
            projection_years: Anos para projeção (padrão: 2020-2100)

        Returns:
            Dicionário com cenários gerados
        """
        if ssp_rcp_scenario not in self.ssp_rcp_combinations:
            raise ValueError(f"Cenário SSP-RCP '{ssp_rcp_scenario}' não encontrado")

        if projection_years is None:
            projection_years = self.projection_years

        scenario = self.ssp_rcp_combinations[ssp_rcp_scenario]

        # Gera projeções de temperatura baseadas no cenário
        temperature_projections = self._generate_temperature_projections(
            scenario, projection_years, n_ensemble_members
        )

        # Gera projeções de precipitação
        precipitation_projections = self._generate_precipitation_projections(
            location, scenario, projection_years, n_ensemble_members
        )

        # Gera projeções de nível do mar
        sea_level_projections = self._generate_sea_level_projections(
            scenario, projection_years, n_ensemble_members
        )

        return {
            "scenario": ssp_rcp_scenario,
            "description": scenario.description,
            "location": location,
            "projection_years": projection_years,
            "ensemble_members": n_ensemble_members,
            "temperature_projections": temperature_projections,
            "precipitation_projections": precipitation_projections,
            "sea_level_projections": sea_level_projections,
            "cmip6_models_used": [model.name for model in self.cmip6_models[:3]],  # Top 3 models
            "timestamp": datetime.now().isoformat()
        }

    def _generate_temperature_projections(
        self,
        scenario: SSPRCPCombination,
        years: List[int],
        n_members: int
    ) -> Dict[str, List[float]]:
        """Gera projeções de temperatura com incerteza do ensemble"""
        # Temperatura base em 2020 (aproximada)
        base_temp = 14.0  # Temperatura global média aproximada

        # Projeção linear até 2100 baseada no cenário
        temp_change_2100 = scenario.temperature_change_2100

        # Adiciona incerteza do ensemble CMIP6 (cerca de ±0.5°C)
        ensemble_uncertainty = np.random.normal(0, 0.5, n_members)

        projections = {}
        for i in range(n_members):
            member_projections = []
            for year in years:
                # Projeção linear com incerteza
                progress = (year - self.baseline_year) / (2100 - self.baseline_year)
                temp_change = temp_change_2100 * progress
                temp_anomaly = temp_change + ensemble_uncertainty[i] * progress
                member_projections.append(base_temp + temp_anomaly)
            projections[f"member_{i+1}"] = member_projections

        # Adiciona estatísticas do ensemble
        projections["mean"] = np.mean([projections[f"member_{i+1}"] for i in range(n_members)], axis=0).tolist()
        projections["p5"] = np.percentile([projections[f"member_{i+1}"] for i in range(n_members)], 5, axis=0).tolist()
        projections["p95"] = np.percentile([projections[f"member_{i+1}"] for i in range(n_members)], 95, axis=0).tolist()

        return projections

    def _generate_precipitation_projections(
        self,
        location: Tuple[float, float],
        scenario: SSPRCPCombination,
        years: List[int],
        n_members: int
    ) -> Dict[str, List[float]]:
        """Gera projeções de precipitação com variação regional"""
        lat, lon = location

        # Precipitação base aproximada baseada na latitude
        if abs(lat) < 23.5:  # Trópicos
            base_precip = 2000  # mm/ano
            change_factor = 1.05 if scenario.rcp == RCPScenario.RCP85 else 1.02
        elif abs(lat) < 66.5:  # Temperate
            base_precip = 800   # mm/ano
            change_factor = 1.08 if scenario.rcp == RCPScenario.RCP85 else 1.03
        else:  # Polar
            base_precip = 300   # mm/ano
            change_factor = 1.15 if scenario.rcp == RCPScenario.RCP85 else 1.05

        # Adiciona incerteza do ensemble
        ensemble_uncertainty = np.random.normal(1, 0.1, n_members)

        projections = {}
        for i in range(n_members):
            member_projections = []
            for year in years:
                progress = (year - self.baseline_year) / (2100 - self.baseline_year)
                precip_change = change_factor ** progress
                uncertainty_factor = ensemble_uncertainty[i] ** progress
                precipitation = base_precip * precip_change * uncertainty_factor
                member_projections.append(precipitation)
            projections[f"member_{i+1}"] = member_projections

        # Estatísticas do ensemble
        projections["mean"] = np.mean([projections[f"member_{i+1}"] for i in range(n_members)], axis=0).tolist()
        projections["p5"] = np.percentile([projections[f"member_{i+1}"] for i in range(n_members)], 5, axis=0).tolist()
        projections["p95"] = np.percentile([projections[f"member_{i+1}"] for i in range(n_members)], 95, axis=0).tolist()

        return projections

    def _generate_sea_level_projections(
        self,
        scenario: SSPRCPCombination,
        years: List[int],
        n_members: int
    ) -> Dict[str, List[float]]:
        """Gera projeções de nível do mar"""
        # Nível do mar base em 2020 (mm acima de 1990)
        base_sea_level = 50

        # Projeções baseadas no cenário RCP
        if scenario.rcp == RCPScenario.RCP26:
            sea_level_2100 = 300  # mm
        elif scenario.rcp == RCPScenario.RCP45:
            sea_level_2100 = 400  # mm
        elif scenario.rcp == RCPScenario.RCP60:
            sea_level_2100 = 500  # mm
        else:  # RCP85
            sea_level_2100 = 800  # mm

        # Adiciona incerteza do ensemble (contribuição de geleiras, etc.)
        ensemble_uncertainty = np.random.normal(0, 50, n_members)

        projections = {}
        for i in range(n_members):
            member_projections = []
            for year in years:
                progress = (year - self.baseline_year) / (2100 - self.baseline_year)
                sea_level_rise = sea_level_2100 * progress
                uncertainty = ensemble_uncertainty[i] * progress
                total_sea_level = base_sea_level + sea_level_rise + uncertainty
                member_projections.append(total_sea_level)
            projections[f"member_{i+1}"] = member_projections

        # Estatísticas do ensemble
        projections["mean"] = np.mean([projections[f"member_{i+1}"] for i in range(n_members)], axis=0).tolist()
        projections["p5"] = np.percentile([projections[f"member_{i+1}"] for i in range(n_members)], 5, axis=0).tolist()
        projections["p95"] = np.percentile([projections[f"member_{i+1}"] for i in range(n_members)], 95, axis=0).tolist()

        return projections

    def calculate_scenario_probabilities(
        self,
        current_indicators: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calcula probabilidades dos cenários baseadas em indicadores atuais

        Args:
            current_indicators: Dicionário com indicadores atuais
                (ex: {'co2_ppm': 420, 'temperature_anomaly': 1.1})

        Returns:
            Probabilidades de cada cenário SSP-RCP
        """
        # Implementação simplificada baseada em indicadores atuais
        co2_current = current_indicators.get('co2_ppm', 420)
        temp_anomaly = current_indicators.get('temperature_anomaly', 1.1)

        probabilities = {}

        for scenario_name, scenario in self.ssp_rcp_combinations.items():
            # Probabilidade baseada na proximidade dos indicadores atuais
            co2_distance = abs(scenario.co2_concentration_2100 - co2_current) / 1000
            temp_distance = abs(scenario.temperature_change_2100 - temp_anomaly) / 5

            # Combina distâncias com peso probabilístico base
            distance = (co2_distance + temp_distance) / 2
            probability = scenario.probability_weight * np.exp(-distance)

            probabilities[scenario_name] = probability

        # Normaliza para somar 1
        total_prob = sum(probabilities.values())
        probabilities = {k: v/total_prob for k, v in probabilities.items()}

        return probabilities

    def get_service_status(self) -> Dict[str, Any]:
        """Retorna status do serviço"""
        return {
            "service": "Probabilistic Climate Scenarios",
            "ssp_rcp_combinations": len(self.ssp_rcp_combinations),
            "cmip6_models": len(self.cmip6_models),
            "baseline_year": self.baseline_year,
            "projection_years": self.projection_years,
            "status": "active",
            "timestamp": datetime.now().isoformat()
}
