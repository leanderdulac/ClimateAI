"""
Endpoints para geocodificação e busca de localidades
"""
from fastapi import APIRouter, Query
from typing import Dict, List, Optional
from services.geocoding_service import GeocodingService

router = APIRouter()
geocoding_service = GeocodingService()

@router.get("/cep/{cep}")
async def get_location_by_cep(
    cep: str
) -> Dict:
    """
    Obtém informações de localização a partir de um CEP
    """
    return await geocoding_service.get_location_from_cep(cep)

@router.get("/cidade")
async def get_location_by_city(
    cidade: str = Query(..., description="Nome da cidade"),
    estado: str = Query(..., min_length=2, max_length=2, description="UF (2 letras)")
) -> Dict:
    """
    Obtém informações de localização a partir de uma cidade e estado
    """
    return await geocoding_service.get_location_from_city_state(cidade, estado)

@router.get("/cidade/busca")
async def search_cities(
    termo: str = Query(..., description="Termo de busca para cidades"),
    estado: Optional[str] = Query(None, description="UF opcional para filtrar resultados")
) -> List[Dict]:
    """
    Faz uma busca parcial por cidades usando o dataset local
    """
    return await geocoding_service.search_cities(termo, estado)

@router.get("/endereco")
async def get_location_by_address(
    endereco: str = Query(..., description="Endereço completo para busca")
) -> Dict:
    """
    Obtém coordenadas a partir de um endereço
    """
    return await geocoding_service.geocode_address(endereco)

@router.get("/coordenadas")
async def get_location_by_coordinates(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude do ponto"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude do ponto")
) -> Dict:
    """
    Obtém informações de endereço a partir de coordenadas
    """
    return await geocoding_service.reverse_geocode(latitude, longitude)
