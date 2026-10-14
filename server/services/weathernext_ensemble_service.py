"""
Google WeatherNext 2 ensemble client via the Open-Meteo Ensemble API.

License: Open-Meteo non-commercial free tier does not require a key.
Commercial use requires OPEN_METEO_API_KEY (or OPENMETEO_API_KEY) and
the customer host https://customer-ensemble-api.open-meteo.com.
See https://open-meteo.com/en/license
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import httpx

from services.ibge_municipalities import get_municipality
from services.weathernext_prob import (
    HEAVY_RAIN_MM,
    apply_exceedance_loading,
    daily_to_dict,
    pricing_exceedance_inputs,
    process_open_meteo_hourly,
    weathernext_oracle_vote,
)

logger = logging.getLogger(__name__)

MODEL_ID = "google_weathernext2_ensemble"
FREE_ENSEMBLE_URL = "https://ensemble-api.open-meteo.com/v1/ensemble"
CUSTOMER_ENSEMBLE_URL = "https://customer-ensemble-api.open-meteo.com/v1/ensemble"

# IBGE-aligned mainland Brazil bounding box (slightly padded).
BRAZIL_BBOX = {
    "lat_min": -34.0,
    "lat_max": 5.5,
    "lon_min": -74.1,
    "lon_max": -32.3,
}

DEFAULT_CACHE_TTL_SECONDS = 2 * 3600  # 2h, within the 1–3h window
DEFAULT_COORD_DECIMALS = 1
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_RETRIES = 3
DEFAULT_BATCH_SIZE = 20
DEFAULT_GRID_RESOLUTION = 1.0
MIN_GRID_RESOLUTION = 0.5
MAX_GRID_RESOLUTION = 2.0
DEFAULT_INTER_CHUNK_DELAY = 0.2

LICENSE_NOTICE = {
    "provider": "Open-Meteo",
    "model": MODEL_ID,
    "terms": (
        "Non-commercial free tier may call ensemble-api.open-meteo.com without a key. "
        "Commercial use requires an Open-Meteo API key and the customer endpoint."
    ),
    "url": "https://open-meteo.com/en/license",
}


class OutsideBrazilError(ValueError):
    """Coordinate is outside the Brazil bounding box."""


class WeatherNextDisabledError(RuntimeError):
    """Raised when WEATHERNEXT_ENABLED is false."""


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class WeatherNextEnsembleService:
    def __init__(
        self,
        *,
        enabled: Optional[bool] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        cache_ttl: Optional[int] = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        retries: int = DEFAULT_RETRIES,
        batch_size: int = DEFAULT_BATCH_SIZE,
        coord_decimals: int = DEFAULT_COORD_DECIMALS,
        inter_chunk_delay: float = DEFAULT_INTER_CHUNK_DELAY,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.enabled = (
            _env_flag("WEATHERNEXT_ENABLED", True) if enabled is None else enabled
        )
        self.api_key = api_key if api_key is not None else _open_meteo_api_key()
        self.base_url = (base_url or _ensemble_base_url(self.api_key)).rstrip("/")
        self.cache_ttl = int(
            cache_ttl
            if cache_ttl is not None
            else os.getenv("WEATHERNEXT_CACHE_TTL", DEFAULT_CACHE_TTL_SECONDS)
        )
        self.timeout = timeout
        self.retries = retries
        self.batch_size = max(1, batch_size)
        self.coord_decimals = coord_decimals
        self.inter_chunk_delay = inter_chunk_delay
        self._http_client = http_client
        self._owns_client = http_client is None
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._cache_lock = asyncio.Lock()

    def require_enabled(self) -> None:
        if not self.enabled:
            raise WeatherNextDisabledError("WEATHERNEXT_ENABLED is false")

    @staticmethod
    def in_brazil(lat: float, lon: float) -> bool:
        return (
            BRAZIL_BBOX["lat_min"] <= lat <= BRAZIL_BBOX["lat_max"]
            and BRAZIL_BBOX["lon_min"] <= lon <= BRAZIL_BBOX["lon_max"]
        )

    def validate_brazil(self, lat: float, lon: float) -> None:
        if not self.in_brazil(lat, lon):
            raise OutsideBrazilError(
                f"Coordinates ({lat}, {lon}) are outside the Brazil bounding box "
                f"{BRAZIL_BBOX}"
            )

    def round_coord(self, value: float) -> float:
        return round(float(value), self.coord_decimals)

    def cache_key(self, lat: float, lon: float, extra: str = "") -> str:
        rounded = f"{self.round_coord(lat):.{self.coord_decimals}f}:{self.round_coord(lon):.{self.coord_decimals}f}"
        raw = f"weathernext:{MODEL_ID}:{rounded}:{extra}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def forecast_point(
        self,
        lat: float,
        lon: float,
        *,
        include_members: bool = False,
        forecast_days: int = 7,
    ) -> Dict[str, Any]:
        self.require_enabled()
        self.validate_brazil(lat, lon)
        payloads = await self._fetch_locations([(lat, lon)], forecast_days=forecast_days)
        if not payloads:
            raise httpx.HTTPError("Empty WeatherNext ensemble response")
        return self._build_location_result(
            payloads[0], lat, lon, include_members=include_members
        )

    async def forecast_batch(
        self,
        coordinates: Sequence[Tuple[float, float]],
        *,
        include_members: bool = False,
        forecast_days: int = 7,
    ) -> List[Dict[str, Any]]:
        self.require_enabled()
        cleaned: List[Tuple[float, float]] = []
        for lat, lon in coordinates:
            self.validate_brazil(lat, lon)
            cleaned.append((float(lat), float(lon)))
        payloads = await self._fetch_locations(cleaned, forecast_days=forecast_days)
        results = []
        for (lat, lon), payload in zip(cleaned, payloads):
            results.append(
                self._build_location_result(
                    payload, lat, lon, include_members=include_members
                )
            )
        return results

    async def forecast_municipality(
        self,
        ibge_code: str,
        *,
        include_members: bool = False,
        forecast_days: int = 7,
    ) -> Dict[str, Any]:
        municipality = get_municipality(ibge_code)
        result = await self.forecast_point(
            float(municipality["latitude"]),
            float(municipality["longitude"]),
            include_members=include_members,
            forecast_days=forecast_days,
        )
        result["municipality"] = municipality
        return result

    async def forecast_brazil_grid(
        self,
        *,
        resolution: float = DEFAULT_GRID_RESOLUTION,
        forecast_days: int = 7,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        self.require_enabled()
        resolution = self._clamp_resolution(resolution)
        cache_key = f"brazil_grid:{resolution}:{forecast_days}"
        if not force_refresh:
            cached = await self._cache_get(cache_key)
            if cached is not None:
                return cached

        points = generate_brazil_grid(resolution)
        cells: List[Dict[str, Any]] = []
        for chunk in _chunks(points, self.batch_size):
            payloads = await self._fetch_locations(chunk, forecast_days=forecast_days)
            for (lat, lon), payload in zip(chunk, payloads):
                result = self._build_location_result(payload, lat, lon, include_members=False)
                exceedance = result.get("pricing_exceedance") or {}
                cells.append(
                    {
                        "lat": lat,
                        "lon": lon,
                        "p_heavy_rain": exceedance.get("p_heavy_rain", 0.0),
                        "precip_exceedance": exceedance.get("precip_exceedance", {}),
                        "heat_exceedance": exceedance.get("heat_exceedance", {}),
                        "horizon_days": exceedance.get("horizon_days", 0),
                    }
                )
            if self.inter_chunk_delay:
                await asyncio.sleep(self.inter_chunk_delay)

        summary = {
            "resolution_deg": resolution,
            "cell_count": len(cells),
            "bbox": BRAZIL_BBOX,
            "heavy_rain_threshold_mm": HEAVY_RAIN_MM,
            "p_heavy_rain_mean": _mean([c["p_heavy_rain"] for c in cells]),
            "p_heavy_rain_max": max((c["p_heavy_rain"] for c in cells), default=0.0),
            "cells": cells,
            "cached": False,
            "license": LICENSE_NOTICE,
            "model": MODEL_ID,
            "timezone_daily": "America/Sao_Paulo",
        }
        await self._cache_set(cache_key, summary)
        summary["cached"] = True
        return summary

    def oracle_vote(
        self,
        location_result: Dict[str, Any],
        *,
        trigger_type: str,
        threshold: float,
        condition: str = "above",
        probability_cutoff: float = 0.5,
    ) -> Dict[str, Any]:
        from services.weathernext_prob import DailyEnsembleStats

        daily_payloads = location_result.get("daily") or []
        daily = [
            DailyEnsembleStats(
                date=day["date"],
                member_count=day.get("member_count", 0),
                temperature_mean_c=day.get("temperature_mean_c", float("nan")),
                temperature_min_c=day.get("temperature_min_c", float("nan")),
                temperature_max_c=day.get("temperature_max_c", float("nan")),
                precip_mean_mm=day.get("precip_mean_mm", 0.0),
                precip_min_mm=day.get("precip_min_mm", 0.0),
                precip_max_mm=day.get("precip_max_mm", 0.0),
                temperature_p10_c=day.get("temperature_p10_c", float("nan")),
                temperature_p50_c=day.get("temperature_p50_c", float("nan")),
                temperature_p90_c=day.get("temperature_p90_c", float("nan")),
                precip_p10_mm=day.get("precip_p10_mm", 0.0),
                precip_p50_mm=day.get("precip_p50_mm", 0.0),
                precip_p90_mm=day.get("precip_p90_mm", 0.0),
                precip_exceedance=day.get("precip_exceedance") or {},
                heat_exceedance=day.get("heat_exceedance") or {},
                p_heavy_rain=day.get("p_heavy_rain", 0.0),
                members=[],
            )
            for day in daily_payloads
        ]
        return weathernext_oracle_vote(
            daily,
            trigger_type=trigger_type,
            threshold=threshold,
            condition=condition,
            probability_cutoff=probability_cutoff,
        )

    @staticmethod
    def premium_with_exceedance(
        base_premium: float,
        exceedance_probability: float,
        loading_factor: float = 0.25,
    ) -> float:
        return apply_exceedance_loading(base_premium, exceedance_probability, loading_factor)

    async def close(self) -> None:
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    def _build_location_result(
        self,
        payload: Dict[str, Any],
        lat: float,
        lon: float,
        *,
        include_members: bool,
    ) -> Dict[str, Any]:
        fan, daily, meta = process_open_meteo_hourly(
            payload, include_members=include_members
        )
        exceedance = pricing_exceedance_inputs(daily)
        return {
            "latitude": payload.get("latitude", lat),
            "longitude": payload.get("longitude", lon),
            "requested": {"lat": lat, "lon": lon},
            "model": MODEL_ID,
            "hourly_fan": fan,
            "daily": [daily_to_dict(day) for day in daily],
            "pricing_exceedance": exceedance,
            "meta": meta,
            "license": LICENSE_NOTICE,
            "timezone_daily": "America/Sao_Paulo",
        }

    async def _fetch_locations(
        self,
        coordinates: Sequence[Tuple[float, float]],
        *,
        forecast_days: int,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for chunk in _chunks(list(coordinates), self.batch_size):
            cached_hits: List[Optional[Dict[str, Any]]] = []
            missing: List[Tuple[int, Tuple[float, float]]] = []
            for idx, (lat, lon) in enumerate(chunk):
                key = self.cache_key(lat, lon, extra=f"days={forecast_days}")
                cached = await self._cache_get(key)
                cached_hits.append(cached)
                if cached is None:
                    missing.append((idx, (lat, lon)))

            fetched: Dict[int, Dict[str, Any]] = {}
            if missing:
                raw_list = await self._http_ensemble(
                    [coord for _, coord in missing], forecast_days=forecast_days
                )
                for (idx, (lat, lon)), raw in zip(missing, raw_list):
                    key = self.cache_key(lat, lon, extra=f"days={forecast_days}")
                    await self._cache_set(key, raw)
                    fetched[idx] = raw

            for idx, cached in enumerate(cached_hits):
                results.append(fetched[idx] if cached is None else cached)
        return results

    async def _http_ensemble(
        self,
        coordinates: Sequence[Tuple[float, float]],
        *,
        forecast_days: int,
    ) -> List[Dict[str, Any]]:
        params = {
            "latitude": ",".join(f"{lat:.4f}" for lat, _ in coordinates),
            "longitude": ",".join(f"{lon:.4f}" for _, lon in coordinates),
            "hourly": "temperature_2m,precipitation",
            "models": MODEL_ID,
            "forecast_days": str(forecast_days),
            "timezone": "UTC",
        }
        if self.api_key:
            params["apikey"] = self.api_key

        last_error: Optional[Exception] = None
        for attempt in range(1, self.retries + 1):
            try:
                client = await self._client()
                response = await client.get(self.base_url, params=params)
                if response.status_code in {429, 500, 502, 503, 504}:
                    raise httpx.HTTPStatusError(
                        f"Open-Meteo ensemble HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                payload = response.json()
                return _normalize_ensemble_payload(payload, len(coordinates))
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_error = exc
                delay = min(2 ** (attempt - 1), 8)
                logger.warning(
                    "WeatherNext ensemble request failed (attempt %s/%s): %s",
                    attempt,
                    self.retries,
                    exc,
                )
                if attempt < self.retries:
                    await asyncio.sleep(delay)
        raise httpx.HTTPError(f"WeatherNext ensemble request failed: {last_error}")

    async def _client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=5.0),
                headers={"User-Agent": "ClimateWise-WeatherNext/1.0"},
            )
        return self._http_client

    async def _cache_get(self, key: str) -> Optional[Any]:
        async with self._cache_lock:
            entry = self._memory_cache.get(key)
            if entry and entry.expires_at > time.time():
                return entry.value
            if entry:
                self._memory_cache.pop(key, None)
        return None

    async def _cache_set(self, key: str, value: Any) -> None:
        async with self._cache_lock:
            self._memory_cache[key] = CacheEntry(
                value=value, expires_at=time.time() + self.cache_ttl
            )

    @staticmethod
    def _clamp_resolution(resolution: float) -> float:
        value = float(resolution)
        if value < MIN_GRID_RESOLUTION:
            return MIN_GRID_RESOLUTION
        if value > MAX_GRID_RESOLUTION:
            return MAX_GRID_RESOLUTION
        return value


_service: Optional[WeatherNextEnsembleService] = None


def get_weathernext_service() -> WeatherNextEnsembleService:
    global _service
    if _service is None:
        _service = WeatherNextEnsembleService()
    return _service


def reset_weathernext_service() -> None:
    global _service
    _service = None


def generate_brazil_grid(resolution: float) -> List[Tuple[float, float]]:
    step = float(resolution)
    points: List[Tuple[float, float]] = []
    lat = BRAZIL_BBOX["lat_min"]
    while lat <= BRAZIL_BBOX["lat_max"] + 1e-9:
        lon = BRAZIL_BBOX["lon_min"]
        while lon <= BRAZIL_BBOX["lon_max"] + 1e-9:
            points.append((round(lat, 4), round(lon, 4)))
            lon += step
        lat += step
    return points


def _normalize_ensemble_payload(payload: Any, expected: int) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if expected == 1:
        return [payload]
    # Open-Meteo multi-location: arrays aligned with the request order.
    if isinstance(payload, dict) and isinstance(payload.get("latitude"), list):
        count = len(payload["latitude"])
        split: List[Dict[str, Any]] = []
        for idx in range(count):
            item = {
                key: (value[idx] if isinstance(value, list) and key != "hourly" else value)
                for key, value in payload.items()
            }
            hourly = payload.get("hourly") or {}
            if isinstance(hourly, list):
                item["hourly"] = hourly[idx]
            split.append(item)
        return split
    return [payload]


def _chunks(items: Sequence[Any], size: int) -> Iterable[List[Any]]:
    for start in range(0, len(items), size):
        yield list(items[start : start + size])


def _mean(values: Sequence[float]) -> float:
    clean = [float(v) for v in values if v is not None]
    return round(sum(clean) / len(clean), 4) if clean else 0.0


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _open_meteo_api_key() -> Optional[str]:
    return (
        os.getenv("OPEN_METEO_API_KEY")
        or os.getenv("OPENMETEO_API_KEY")
        or None
    )


def _ensemble_base_url(api_key: Optional[str]) -> str:
    override = os.getenv("OPEN_METEO_ENSEMBLE_URL")
    if override:
        return override
    if api_key:
        return os.getenv("OPEN_METEO_CUSTOMER_ENSEMBLE_URL", CUSTOMER_ENSEMBLE_URL)
    return FREE_ENSEMBLE_URL
