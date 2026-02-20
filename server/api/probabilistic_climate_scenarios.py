"""
API Router para Cenários Probabilísticos Climáticos
Implementa endpoints para SSP-RCP combinations e CMIP6 ensemble models
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.probabilistic_climate_scenarios_service import ProbabilisticClimateScenariosService

logger = logging.getLogger(__name__)

router = APIRouter()
service = ProbabilisticClimateScenariosService()


class ClimateScenarioRequest(BaseModel):
    """Request para geração de cenários climáticos"""
    latitude: float = Field(..., description="Latitude da localização", ge=-90, le=90)
    longitude: float = Field(..., description="Longitude da localização", ge=-180, le=180)
    ssp_rcp_scenario: str = Field(..., description="Cenário SSP-RCP (ex: 'SSP2-RCP4.5')")
    n_ensemble_members: int = Field(10, description="Número de membros do ensemble", ge=1, le=50)
    projection_years: Optional[List[int]] = Field(None, description="Anos para projeção (2020-2100)")


class ScenarioProbabilitiesRequest(BaseModel):
    """Request para cálculo de probabilidades de cenários"""
    co2_ppm: float = Field(420, description="Concentração atual de CO2 (ppm)")
    temperature_anomaly: float = Field(1.1, description="Anomalia de temperatura atual (°C)")


@router.get("/ssp-rcp-combinations")
async def get_ssp_rcp_combinations():
    """
    Retorna todas as combinações SSP-RCP disponíveis
    """
    try:
        combinations = service.get_ssp_rcp_combinations()
        return {
            "combinations": combinations,
            "count": len(combinations),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao obter combinações SSP-RCP: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/cmip6-models")
async def get_cmip6_models():
    """
    Retorna informações sobre modelos CMIP6 disponíveis
    """
    try:
        models = service.get_cmip6_models()
        return {
            "models": models,
            "count": len(models),
            "total_ensemble_members": sum(model["ensemble_members"] for model in models),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao obter modelos CMIP6: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/generate-scenarios")
async def generate_climate_scenarios(request: ClimateScenarioRequest):
    """
    Gera cenários climáticos usando SSP-RCP e ensemble CMIP6
    """
    try:
        # Valida se o cenário existe
        available_scenarios = service.get_ssp_rcp_combinations()
        if request.ssp_rcp_scenario not in available_scenarios:
            raise HTTPException(
                status_code=400,
                detail=f"Cenário '{request.ssp_rcp_scenario}' não encontrado. Cenários disponíveis: {list(available_scenarios.keys())}"
            )

        # Gera cenários
        result = service.generate_climate_scenarios(
            location=(request.latitude, request.longitude),
            ssp_rcp_scenario=request.ssp_rcp_scenario,
            n_ensemble_members=request.n_ensemble_members,
            projection_years=request.projection_years
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao gerar cenários climáticos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/scenario-probabilities")
async def calculate_scenario_probabilities(request: ScenarioProbabilitiesRequest):
    """
    Calcula probabilidades dos cenários SSP-RCP baseadas em indicadores atuais
    """
    try:
        current_indicators = {
            "co2_ppm": request.co2_ppm,
            "temperature_anomaly": request.temperature_anomaly
        }

        probabilities = service.calculate_scenario_probabilities(current_indicators)

        # Ordena por probabilidade decrescente
        sorted_probabilities = dict(sorted(probabilities.items(), key=lambda x: x[1], reverse=True))

        return {
            "current_indicators": current_indicators,
            "scenario_probabilities": sorted_probabilities,
            "most_likely_scenario": list(sorted_probabilities.keys())[0],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erro ao calcular probabilidades de cenários: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/scenario/{scenario_name}")
async def get_scenario_details(scenario_name: str):
    """
    Retorna detalhes de um cenário SSP-RCP específico
    """
    try:
        combinations = service.get_ssp_rcp_combinations()

        if scenario_name not in combinations:
            raise HTTPException(
                status_code=404,
                detail=f"Cenário '{scenario_name}' não encontrado. Cenários disponíveis: {list(combinations.keys())}"
            )

        scenario = combinations[scenario_name]

        # Adiciona informações adicionais
        scenario["climate_impacts"] = {
            "extreme_heat_days": "Aumento significativo" if scenario["temperature_change_2100"] > 3.0 else "Moderado",
            "precipitation_change": "Aumento" if scenario["rcp"] in ["RCP8.5", "RCP6.0"] else "Variável",
            "sea_level_rise": f"{scenario['temperature_change_2100'] * 3:.1f} mm até 2100 (aproximado)",
            "adaptation_needs": "Alto" if scenario["temperature_change_2100"] > 3.5 else "Médio" if scenario["temperature_change_2100"] > 2.5 else "Baixo"
        }

        return {
            "scenario": scenario_name,
            "details": scenario,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter detalhes do cenário: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/status")
async def get_service_status():
    """
    Retorna status do serviço de cenários probabilísticos
    """
    try:
        status = service.get_service_status()
        return status
    except Exception as e:
        logger.error(f"Erro ao obter status do serviço: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/available-scenarios")
async def get_available_scenarios():
    """
    Retorna lista de cenários disponíveis com descrições
    """
    try:
        combinations = service.get_ssp_rcp_combinations()

        scenarios_list = []
        for name, details in combinations.items():
            scenarios_list.append({
                "name": name,
                "ssp": details["ssp"],
                "rcp": details["rcp"],
                "description": details["description"],
                "temperature_change_2100": details["temperature_change_2100"],
                "co2_concentration_2100": details["co2_concentration_2100"],
                "probability_weight": details["probability_weight"]
            })

        return {
            "scenarios": scenarios_list,
            "total_scenarios": len(scenarios_list),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erro ao obter cenários disponíveis: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")