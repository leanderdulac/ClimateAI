"""
Endpoints para geocodificação e busca de localidades
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Query, HTTPException

from services.geocoding_service import GeocodingService

router = APIRouter()
geocoding_service = GeocodingService()


@router.get("/cep/{cep}")
async def get_location_by_cep(cep: str) -> Dict:
    """
    Obtém informações de localização a partir de um CEP
    """
    return await geocoding_service.get_location_from_cep(cep)


# Endpoint de busca por cidades (mais específico) - definido antes da rota dinâmica
@router.get("/cidade/busca")
async def search_cities(
    termo: str = Query(..., description="Termo de busca para cidades"),
    estado: Optional[str] = Query(
        None, description="UF opcional para filtrar resultados"
    ),
) -> List[Dict]:
    """
    Faz uma busca parcial por cidades usando o dataset local
    """
    return await geocoding_service.search_cities(termo, estado)


# Novo endpoint: busca por cidade via rota /cidade/{nome} e UF opcional
@router.get("/cidade/{nome}")
async def get_location_by_city_route(
    nome: str,
    estado: Optional[str] = Query(None, min_length=2, max_length=2, description="UF (2 letras) opcional")
) -> Dict:
    """
    Obtém informações de localização a partir de uma cidade (e UF opcional)
    """
    if estado:
        return await geocoding_service.get_location_from_city_state(nome, estado)
    # Fallback: busca parcial
    cidades = await geocoding_service.search_cities(nome)
    if not cidades:
        raise HTTPException(status_code=404, detail="Cidade não encontrada")
    return cidades[0]


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
    longitude: float = Query(..., ge=-180, le=180, description="Longitude do ponto"),
) -> Dict:
    """
    Obtém informações de endereço a partir de coordenadas
    """
    return await geocoding_service.reverse_geocode(latitude, longitude)
