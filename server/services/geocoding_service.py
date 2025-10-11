"""
Serviço para geocodificação de endereços e CEPs com suporte offline básico.
"""
import asyncio
import json
import math
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
import pycep_correios

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "br_cities.json"
EARTH_RADIUS_KM = 6371.0


class GeocodingService:
    def __init__(self):
        """
        Inicializa o serviço de geocodificação com Nominatim (OpenStreetMap),
        integrações com os Correios para CEP e um índice local de capitais brasileiras
        para operação offline.
        """
        self.geolocator = Nominatim(
            user_agent="climateai/1.0",
            timeout=10
        )
        self.cache: Dict[str, Dict] = {}
        self.city_data = self._load_city_dataset()
        self.city_index = {
            self._build_key(entry["city"], entry["state"]): entry
            for entry in self.city_data
        }

    async def get_location_from_cep(self, cep: str) -> Dict:
        """
        Obtém informações de localização a partir de um CEP.
        """
        normalized = cep.replace('-', '').replace('.', '').strip()
        if not normalized:
            raise HTTPException(status_code=400, detail="CEP inválido")

        if normalized in self.cache:
            return self.cache[normalized]

        try:
            address_data = await asyncio.to_thread(
                pycep_correios.get_address_from_cep,
                normalized
            )
        except (pycep_correios.exceptions.InvalidCEP,
                pycep_correios.exceptions.CEPNotFound) as exc:
            # Tentar ViaCEP como fallback
            try:
                import requests
                response = requests.get(f"https://viacep.com.br/ws/{normalized}/json/", timeout=10)
                if response.status_code == 200:
                    via_cep_data = response.json()
                    if 'erro' not in via_cep_data:
                        address_data = {
                            'cep': via_cep_data.get('cep'),
                            'logradouro': via_cep_data.get('logradouro'),
                            'bairro': via_cep_data.get('bairro'),
                            'cidade': via_cep_data.get('localidade'),
                            'uf': via_cep_data.get('uf'),
                            'complemento': via_cep_data.get('complemento')
                        }
                    else:
                        raise HTTPException(status_code=404, detail="CEP não encontrado")
                else:
                    raise HTTPException(status_code=response.status_code, detail="Erro na API ViaCEP")
            except Exception:
                # Último fallback: tentar geocodificar como endereço
                try:
                    geo_result = await self.geocode_address(f"Brasil, CEP {normalized}")
                    if geo_result:
                        response = {
                            'latitude': geo_result.get('latitude'),
                            'longitude': geo_result.get('longitude'),
                            'cidade': geo_result.get('cidade'),
                            'estado': geo_result.get('estado'),
                            'cep': normalized,
                            'formatted_address': geo_result.get('formatted_address'),
                            'fonte': 'nominatim_fallback'
                        }
                        self.cache[normalized] = response
                        return response
                except Exception:
                    pass

                # Se chegou aqui, nenhum fallback funcionou
                if isinstance(exc, pycep_correios.exceptions.InvalidCEP):
                    raise HTTPException(status_code=400, detail="CEP inválido") from exc
                else:
                    raise HTTPException(status_code=404, detail="CEP não encontrado") from exc
        except Exception as exc:  # pragma: no cover - fallback defensivo
            # Tentar ViaCEP como último recurso
            try:
                import requests
                response = requests.get(f"https://viacep.com.br/ws/{normalized}/json/", timeout=10)
                if response.status_code == 200:
                    via_cep_data = response.json()
                    if 'erro' not in via_cep_data:
                        address_data = {
                            'cep': via_cep_data.get('cep'),
                            'logradouro': via_cep_data.get('logradouro'),
                            'bairro': via_cep_data.get('bairro'),
                            'cidade': via_cep_data.get('localidade'),
                            'uf': via_cep_data.get('uf'),
                            'complemento': via_cep_data.get('complemento')
                        }
                    else:
                        raise HTTPException(status_code=404, detail="CEP não encontrado")
                else:
                    raise HTTPException(status_code=response.status_code, detail="Erro na API ViaCEP")
            except Exception:
                raise HTTPException(status_code=500, detail=f"Erro ao buscar CEP: {exc}") from exc

        city_name = address_data.get('cidade')
        state_abbr = address_data.get('uf')
        formatted_address = ', '.join(
            filter(
                None,
                [
                    address_data.get('logradouro'),
                    address_data.get('bairro'),
                    f"{city_name} - {state_abbr}" if city_name and state_abbr else None,
                    "Brasil"
                ]
            )
        ) or None

        entry = self._find_city_entry(city_name, state_abbr)
        if entry:
            response = self._city_to_response(
                entry,
                extra={
                    'cep': address_data.get('cep') or normalized,
                    'logradouro': address_data.get('logradouro'),
                    'bairro': address_data.get('bairro'),
                    'complemento': address_data.get('complemento'),
                    'formatted_address': formatted_address
                },
                fallback_city=city_name,
                fallback_state=state_abbr
            )
        else:
            geo = await self.geocode_address(formatted_address or f"{city_name}, {state_abbr}, Brasil")
            response = self._city_to_response(
                None,
                latitude=geo.get('latitude'),
                longitude=geo.get('longitude'),
                extra={
                    'cep': address_data.get('cep') or normalized,
                    'logradouro': address_data.get('logradouro'),
                    'bairro': address_data.get('bairro'),
                    'complemento': address_data.get('complemento'),
                    'formatted_address': geo.get('formatted_address')
                },
                fallback_city=city_name,
                fallback_state=state_abbr
            )

        self.cache[normalized] = response
        return response

    async def geocode_address(self, address: str) -> Dict:
        """
        Converte um endereço em coordenadas geográficas.
        """
        if not address:
            raise HTTPException(status_code=400, detail="Endereço não informado")

        if address in self.cache:
            return self.cache[address]

        city, state = self._extract_city_state(address)
        entry = self._find_city_entry(city, state)
        if entry:
            result = self._city_to_response(entry)
            self.cache[address] = result
            return result

        location = await self._run_with_retries(
            lambda: self.geolocator.geocode(
                address,
                exactly_one=True,
                addressdetails=True,
                language='pt-BR'
            )
        )

        if not location:
            raise HTTPException(status_code=404, detail="Endereço não encontrado")

        raw_address = location.raw.get('address', {})
        result = {
            'latitude': location.latitude,
            'longitude': location.longitude,
            'formatted_address': location.address,
            'city': raw_address.get('city') or raw_address.get('town') or raw_address.get('village'),
            'state': raw_address.get('state'),
            'country': raw_address.get('country'),
            'postcode': raw_address.get('postcode')
        }
        result['cidade'] = result.get('city')
        result['estado'] = result.get('state')

        self.cache[address] = result
        return result

    async def reverse_geocode(self, latitude: float, longitude: float) -> Dict:
        """
        Converte coordenadas geográficas em endereço.
        """
        cache_key = f"{latitude},{longitude}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        entry = self._find_nearest_city(latitude, longitude)
        if entry:
            result = self._city_to_response(
                entry,
                latitude=latitude,
                longitude=longitude,
                extra={'distance_km': entry.get('distance_km')}
            )
            self.cache[cache_key] = result
            return result

        location = await self._run_with_retries(
            lambda: self.geolocator.reverse(
                (latitude, longitude),
                language='pt-BR',
                addressdetails=True
            )
        )

        if not location:
            raise HTTPException(status_code=404, detail="Localização não encontrada")

        address = location.raw.get('address', {})
        result = {
            'formatted_address': location.address,
            'city': address.get('city') or address.get('town') or address.get('village'),
            'state': address.get('state'),
            'country': address.get('country'),
            'postcode': address.get('postcode'),
            'latitude': latitude,
            'longitude': longitude
        }
        result['cidade'] = result.get('city')
        result['estado'] = result.get('state')

        self.cache[cache_key] = result
        return result

    async def get_location_from_city_state(self, city: str, state: str) -> Dict:
        """
        Retorna informações de localização para uma combinação cidade/estado.
        """
        entry = self._find_city_entry(city, state)
        if not entry:
            raise HTTPException(status_code=404, detail="Cidade não encontrada")
        return self._city_to_response(entry)

    async def search_cities(self, query: str, state: Optional[str] = None) -> List[Dict]:
        """
        Retorna uma lista de cidades que contenham o termo informado.
        """
        if not query:
            return []

        normalized_query = self._normalize_text(query)
        state_filter = state.strip().upper() if state else None
        results = [
            self._city_to_response(entry)
            for entry in self.city_data
            if normalized_query in self._normalize_text(entry['city']) and
            (not state_filter or entry['state'] == state_filter)
        ]
        return results[:10]

    async def _run_with_retries(self, func, attempts: int = 3):
        """
        Executa chamada bloqueante em thread separada com tentativas e tratamento
        de timeout específico do Nominatim.
        """
        last_error = None
        for attempt in range(attempts):
            try:
                return await asyncio.to_thread(func)
            except GeocoderTimedOut as exc:
                last_error = exc
                if attempt == attempts - 1:
                    raise HTTPException(
                        status_code=408,
                        detail="Tempo limite excedido na geocodificação"
                    ) from exc
            except Exception as exc:
                last_error = exc
                if attempt == attempts - 1:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Erro na geocodificação: {exc}"
                    ) from exc

        if last_error:
            raise HTTPException(
                status_code=500,
                detail=f"Erro na geocodificação: {last_error}"
            )

        return None

    def _load_city_dataset(self) -> List[Dict]:
        if not DATA_PATH.exists():
            return []
        try:
            with DATA_PATH.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"Falha ao carregar dataset de cidades: {exc}") from exc

        for entry in data:
            entry.setdefault("country", "Brasil")
            entry.setdefault(
                "formatted_address",
                f"{entry['city']} - {entry['state']}, Brasil"
            )
        return data

    def _normalize_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value or "")
        ascii_text = normalized.encode("ASCII", "ignore").decode("ASCII")
        return ascii_text.strip().lower()

    def _build_key(self, city: str, state: str) -> str:
        return f"{self._normalize_text(city)}::{(state or '').strip().upper()}"

    def _find_city_entry(self, city: Optional[str], state: Optional[str]) -> Optional[Dict]:
        if not city or not state:
            return None
        return self.city_index.get(self._build_key(city, state))

    def _find_nearest_city(self, latitude: float, longitude: float) -> Optional[Dict]:
        if not self.city_data:
            return None

        nearest = None
        min_distance = None
        for entry in self.city_data:
            distance = self._haversine(
                latitude,
                longitude,
                entry['latitude'],
                entry['longitude']
            )
            if min_distance is None or distance < min_distance:
                min_distance = distance
                nearest = entry

        if nearest is None:
            return None

        result = dict(nearest)
        result['distance_km'] = min_distance
        return result

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(
            math.radians,
            [lat1, lon1, lat2, lon2]
        )
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return EARTH_RADIUS_KM * c

    def _city_to_response(
        self,
        entry: Optional[Dict],
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        extra: Optional[Dict] = None,
        fallback_city: Optional[str] = None,
        fallback_state: Optional[str] = None
    ) -> Dict:
        if entry is None:
            if latitude is None or longitude is None:
                raise HTTPException(
                    status_code=404,
                    detail="Localização não encontrada"
                )
            response = {
                'latitude': latitude,
                'longitude': longitude,
                'city': fallback_city,
                'cidade': fallback_city,
                'state': fallback_state,
                'estado': fallback_state,
                'formatted_address': (
                    f"{fallback_city} - {fallback_state}, Brasil"
                    if fallback_city and fallback_state else None
                ),
                'country': 'Brasil',
                'pais': 'Brasil'
            }
        else:
            response = {
                'latitude': entry['latitude'] if latitude is None else latitude,
                'longitude': entry['longitude'] if longitude is None else longitude,
                'city': entry['city'],
                'cidade': entry['city'],
                'state': entry['state'],
                'estado': entry['state'],
                'state_name': entry.get('state_name'),
                'estado_nome': entry.get('state_name'),
                'country': entry.get('country', 'Brasil'),
                'pais': entry.get('country', 'Brasil'),
                'formatted_address': entry.get('formatted_address')
            }

        if extra:
            for key, value in extra.items():
                if value is not None:
                    response[key] = value

        return response

    def _extract_city_state(self, address: str) -> Tuple[Optional[str], Optional[str]]:
        parts = [part.strip() for part in address.split(',') if part.strip()]
        if len(parts) < 2:
            return None, None

        possible_state = parts[-1]
        if len(possible_state) == 2 and possible_state.isalpha():
            return parts[-2], possible_state.upper()

        if '-' in possible_state:
            tokens = [token.strip() for token in possible_state.split('-')]
            uf = tokens[-1]
            if len(uf) == 2 and uf.isalpha():
                return parts[-2], uf.upper()

        return parts[-2], None
