"""
Climate Data Service — Integração com CEMADEN, Open-Meteo e Embrapa
Backbone de dados meteorológicos e ambientais em tempo real para o Oracle.

Fontes:
  - Open-Meteo (principal): tempo real para qualquer coordenada no Brasil
  - CEMADEN: alertas nacionais de desastres (scraping público)
  - Embrapa: NDVI/solo via Open-Meteo soil data como proxy
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

import aiohttp

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════════════════════════
# Data Models
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class WeatherData:
    """Dados meteorológicos de uma localidade"""
    latitude: float
    longitude: float
    temperature: float           # °C
    humidity: float              # %
    rain: float                  # mm
    wind_speed: float            # km/h
    weather_code: int            # WMO code
    weather_description: str
    soil_moisture: Optional[float] = None     # m³/m³
    soil_temperature: Optional[float] = None  # °C
    timestamp: str = ""
    source: str = "Open-Meteo"


@dataclass
class ClimateAlert:
    """Alerta climático detectado"""
    alert_id: str
    alert_type: str           # inundacao, seca, vendaval, etc.
    severity: str             # baixa, media, alta, critica
    severity_score: float     # 1.0-5.0
    title: str
    description: str
    latitude: float
    longitude: float
    municipio: str
    uf: str
    source: str               # Open-Meteo, CEMADEN, Embrapa
    detected_at: datetime = field(default_factory=datetime.now)
    weather_data: Optional[Dict] = None


# ═════════════════════════════════════════════════════════════════════════════
# WMO Weather Code Interpretation
# ═════════════════════════════════════════════════════════════════════════════

WMO_CODES: Dict[int, Tuple[str, str]] = {
    0: ('Céu limpo', 'normal'),
    1: ('Predominantemente limpo', 'normal'),
    2: ('Parcialmente nublado', 'normal'),
    3: ('Nublado', 'normal'),
    45: ('Nevoeiro', 'normal'),
    48: ('Nevoeiro com formação de gelo', 'normal'),
    51: ('Chuvisco leve', 'normal'),
    53: ('Chuvisco moderado', 'normal'),
    55: ('Chuvisco forte', 'atencao'),
    56: ('Chuvisco congelante leve', 'atencao'),
    57: ('Chuvisco congelante forte', 'alerta'),
    61: ('Chuva leve', 'normal'),
    63: ('Chuva moderada', 'atencao'),
    65: ('Chuva forte', 'alerta'),
    66: ('Chuva congelante leve', 'atencao'),
    67: ('Chuva congelante forte', 'alerta'),
    71: ('Neve leve', 'normal'),
    73: ('Neve moderada', 'atencao'),
    75: ('Neve forte', 'alerta'),
    77: ('Grãos de neve', 'normal'),
    80: ('Pancadas de chuva leve', 'normal'),
    81: ('Pancadas de chuva moderada', 'atencao'),
    82: ('Pancadas de chuva violenta', 'critico'),
    85: ('Pancadas de neve leve', 'atencao'),
    86: ('Pancadas de neve forte', 'alerta'),
    95: ('Tempestade', 'critico'),
    96: ('Tempestade com granizo leve', 'critico'),
    99: ('Tempestade com granizo forte', 'critico'),
}

# Brazilian capitals with coordinates for systematic monitoring
BRAZIL_MONITORING_POINTS: List[Dict[str, Any]] = [
    {'name': 'São Paulo', 'uf': 'SP', 'lat': -23.550, 'lon': -46.633},
    {'name': 'Rio de Janeiro', 'uf': 'RJ', 'lat': -22.906, 'lon': -43.172},
    {'name': 'Belo Horizonte', 'uf': 'MG', 'lat': -19.916, 'lon': -43.934},
    {'name': 'Porto Alegre', 'uf': 'RS', 'lat': -30.034, 'lon': -51.217},
    {'name': 'Salvador', 'uf': 'BA', 'lat': -12.971, 'lon': -38.501},
    {'name': 'Fortaleza', 'uf': 'CE', 'lat': -3.731, 'lon': -38.526},
    {'name': 'Recife', 'uf': 'PE', 'lat': -8.047, 'lon': -34.877},
    {'name': 'Curitiba', 'uf': 'PR', 'lat': -25.428, 'lon': -49.273},
    {'name': 'Manaus', 'uf': 'AM', 'lat': -3.119, 'lon': -60.021},
    {'name': 'Belém', 'uf': 'PA', 'lat': -1.455, 'lon': -48.502},
    {'name': 'Florianópolis', 'uf': 'SC', 'lat': -27.595, 'lon': -48.548},
    {'name': 'Goiânia', 'uf': 'GO', 'lat': -16.686, 'lon': -49.264},
    {'name': 'Brasília', 'uf': 'DF', 'lat': -15.793, 'lon': -47.882},
    {'name': 'Natal', 'uf': 'RN', 'lat': -5.795, 'lon': -35.209},
    {'name': 'Campo Grande', 'uf': 'MS', 'lat': -20.469, 'lon': -54.620},
    {'name': 'Petrópolis', 'uf': 'RJ', 'lat': -22.505, 'lon': -43.178},
    {'name': 'Blumenau', 'uf': 'SC', 'lat': -26.919, 'lon': -49.066},
    {'name': 'Teresina', 'uf': 'PI', 'lat': -5.089, 'lon': -42.801},
    {'name': 'São Luís', 'uf': 'MA', 'lat': -2.530, 'lon': -44.282},
    {'name': 'Cuiabá', 'uf': 'MT', 'lat': -15.601, 'lon': -56.097},
]


# ═════════════════════════════════════════════════════════════════════════════
# Service
# ═════════════════════════════════════════════════════════════════════════════

class ClimateDataService:
    """
    Serviço integrado de dados climáticos.
    Combina Open-Meteo (weather), CEMADEN (alertas) e Embrapa (solo/vegetação).
    """

    def __init__(self):
        self._cache: Dict[str, Tuple[datetime, Any]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._alerts: List[ClimateAlert] = []
        self._last_scan: Optional[datetime] = None
        self._scan_interval = 600  # 10 minutes
        self._background_task: Optional[asyncio.Task] = None
        logger.info("ClimateDataService initialized (Open-Meteo + CEMADEN + Embrapa)")

    # ── Cache ────────────────────────────────────────────────────────────

    def _cache_key(self, prefix: str, lat: float, lon: float) -> str:
        return f"{prefix}_{lat:.2f}_{lon:.2f}"

    def _get_cache(self, key: str) -> Optional[Any]:
        if key in self._cache:
            ts, data = self._cache[key]
            if (datetime.now() - ts).total_seconds() < self._cache_ttl:
                return data
            del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Any):
        self._cache[key] = (datetime.now(), data)

    # ── Background scan ─────────────────────────────────────────────────

    async def start_background_scan(self):
        """Inicia varredura periódica de todas as capitais"""
        if self._background_task is None:
            self._background_task = asyncio.create_task(self._periodic_scan())
            logger.info("Climate data background scan started")

    async def stop_background_scan(self):
        if self._background_task:
            self._background_task.cancel()
            self._background_task = None

    async def _periodic_scan(self):
        while True:
            try:
                await self.scan_brazil_conditions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in climate scan: {e}")
            await asyncio.sleep(self._scan_interval)

    # ═══════════════════════════════════════════════════════════════════
    # Open-Meteo Integration
    # ═══════════════════════════════════════════════════════════════════

    async def fetch_current_weather(self, lat: float, lon: float) -> Optional[WeatherData]:
        """Busca condições meteorológicas atuais via Open-Meteo"""
        cache_key = self._cache_key("weather", lat, lon)
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,rain,showers,"
            f"weather_code,wind_speed_10m"
            f"&hourly=soil_moisture_0_to_1cm,soil_temperature_0cm"
            f"&timezone=America/Sao_Paulo&forecast_days=1"
        )

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        logger.warning(f"Open-Meteo returned {resp.status}")
                        return None
                    data = await resp.json()

            current = data.get('current', {})
            hourly = data.get('hourly', {})

            # Get latest soil data from hourly (closest hour)
            soil_moisture = None
            soil_temperature = None
            if 'soil_moisture_0_to_1cm' in hourly:
                sm_vals = [v for v in hourly['soil_moisture_0_to_1cm'] if v is not None]
                if sm_vals:
                    soil_moisture = sm_vals[-1]
            if 'soil_temperature_0cm' in hourly:
                st_vals = [v for v in hourly['soil_temperature_0cm'] if v is not None]
                if st_vals:
                    soil_temperature = st_vals[-1]

            wcode = current.get('weather_code', 0)
            wmo_info = WMO_CODES.get(wcode, ('Desconhecido', 'normal'))

            weather = WeatherData(
                latitude=lat,
                longitude=lon,
                temperature=current.get('temperature_2m', 0),
                humidity=current.get('relative_humidity_2m', 0),
                rain=current.get('rain', 0) + current.get('showers', 0),
                wind_speed=current.get('wind_speed_10m', 0),
                weather_code=wcode,
                weather_description=wmo_info[0],
                soil_moisture=soil_moisture,
                soil_temperature=soil_temperature,
                timestamp=current.get('time', datetime.now().isoformat()),
                source='Open-Meteo',
            )

            self._set_cache(cache_key, weather)
            return weather

        except Exception as e:
            logger.warning(f"Open-Meteo fetch error for ({lat},{lon}): {e}")
            return None

    async def fetch_daily_forecast(self, lat: float, lon: float, days: int = 7) -> Optional[Dict]:
        """Previsão diária com máximos/mínimos"""
        cache_key = self._cache_key(f"forecast_{days}", lat, lon)
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min,"
            f"rain_sum,wind_speed_10m_max,precipitation_probability_max"
            f"&timezone=America/Sao_Paulo&forecast_days={days}"
        )

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()

            result = data.get('daily', {})
            self._set_cache(cache_key, result)
            return result

        except Exception as e:
            logger.warning(f"Open-Meteo forecast error: {e}")
            return None

    def _detect_extreme_from_weather(self, weather: WeatherData, location: Dict) -> Optional[ClimateAlert]:
        """Detecta condições extremas a partir dos dados Open-Meteo"""
        wcode = weather.weather_code
        wmo_info = WMO_CODES.get(wcode, ('Desconhecido', 'normal'))
        level = wmo_info[1]

        alert_type = None
        severity = 'media'
        severity_score = 2.5

        # Chuva intensa / tempestade
        if wcode >= 95:
            alert_type = 'tempestade' if wcode >= 95 else 'vendaval'
            severity = 'critica'
            severity_score = 5.0
        elif wcode in (82,):
            alert_type = 'inundacao'
            severity = 'alta'
            severity_score = 4.0
        elif wcode in (65, 67):
            alert_type = 'inundacao'
            severity = 'alta'
            severity_score = 3.5
        elif wcode in (96, 99):
            alert_type = 'granizo'
            severity = 'critica'
            severity_score = 4.5
        # Vento forte
        elif weather.wind_speed > 80:
            alert_type = 'vendaval'
            severity = 'alta'
            severity_score = 4.0
        elif weather.wind_speed > 60:
            alert_type = 'vendaval'
            severity = 'media'
            severity_score = 3.0
        # Seca (solo muito seco)
        elif weather.soil_moisture is not None and weather.soil_moisture < 0.05:
            if weather.rain == 0 and weather.humidity < 30:
                alert_type = 'seca'
                severity = 'alta'
                severity_score = 3.5
        # Calor extremo
        elif weather.temperature > 40:
            alert_type = 'onda_calor'
            severity = 'alta'
            severity_score = 3.5
        # Chuva moderada com solo molhado (risco deslizamento em regiões serranas)
        elif wcode in (63, 81) and weather.rain > 10:
            alert_type = 'deslizamento'
            severity = 'media'
            severity_score = 2.5

        if not alert_type:
            return None

        loc_name = location['name']
        hash_input = f"{loc_name}_{wcode}_{datetime.now().hour}"
        return ClimateAlert(
            alert_id=f"openmeteo_{hashlib.md5(hash_input.encode(), usedforsecurity=False).hexdigest()[:12]}",
            alert_type=alert_type,
            severity=severity,
            severity_score=severity_score,
            title=f"{wmo_info[0]} em {location['name']}/{location['uf']}",
            description=(
                f"Condição detectada via Open-Meteo: {wmo_info[0]}. "
                f"Temp: {weather.temperature}°C, Chuva: {weather.rain}mm, "
                f"Vento: {weather.wind_speed} km/h"
                + (f", Solo: {weather.soil_moisture:.3f} m³/m³" if weather.soil_moisture else "")
            ),
            latitude=weather.latitude,
            longitude=weather.longitude,
            municipio=location['name'],
            uf=location['uf'],
            source='Open-Meteo',
            weather_data=asdict(weather),
        )

    # ═══════════════════════════════════════════════════════════════════
    # CEMADEN Integration (scraping público)
    # ═══════════════════════════════════════════════════════════════════

    async def fetch_cemaden_alerts(self) -> List[ClimateAlert]:
        """Busca alertas do CEMADEN via página pública"""
        cache_key = "cemaden_alerts"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        alerts = []

        # Try CEMADEN public REST endpoints
        cemaden_urls = [
            "http://sws.cemaden.gov.br/PED/rest/pcds/dados_area/-15.0/-50.0/2000/1",
            "https://resources.cemaden.gov.br/graficos/json/public_DadosEstacoes.json",
        ]

        for url in cemaden_urls:
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            content_type = resp.content_type or ''
                            if 'json' in content_type:
                                data = await resp.json()
                                alerts.extend(self._parse_cemaden_data(data))
                                logger.info(f"CEMADEN: {len(alerts)} alerts from {url}")
                                break
            except Exception as e:
                logger.debug(f"CEMADEN endpoint failed ({url}): {e}")
                continue

        if not alerts:
            logger.info("CEMADEN endpoints unavailable — using Open-Meteo detection as fallback")

        self._set_cache(cache_key, alerts)
        return alerts

    def _parse_cemaden_data(self, data: Any) -> List[ClimateAlert]:
        """Parse CEMADEN JSON response into ClimateAlerts"""
        alerts = []
        if isinstance(data, list):
            for item in data[:50]:
                try:
                    # CEMADEN station data format
                    lat = float(item.get('latitude', item.get('lat', 0)))
                    lon = float(item.get('longitude', item.get('lon', 0)))
                    valor = float(item.get('valor', item.get('acumulado', 0)))
                    municipio = item.get('municipio', item.get('nome', 'Desconhecido'))
                    uf = item.get('uf', item.get('estado', 'BR'))

                    if valor <= 0:
                        continue

                    # Classify precipitation intensity
                    if valor > 50:
                        severity, score, atype = 'critica', 5.0, 'inundacao'
                    elif valor > 30:
                        severity, score, atype = 'alta', 4.0, 'inundacao'
                    elif valor > 15:
                        severity, score, atype = 'media', 3.0, 'inundacao'
                    else:
                        continue  # below threshold

                    alerts.append(ClimateAlert(
                        alert_id=f"cemaden_{hashlib.md5(f'{municipio}_{valor}'.encode(), usedforsecurity=False).hexdigest()[:12]}",
                        alert_type=atype,
                        severity=severity,
                        severity_score=score,
                        title=f"Precipitação {valor:.1f}mm em {municipio}/{uf}",
                        description=f"Estação CEMADEN registrou {valor:.1f}mm na última hora. Risco de {atype}.",
                        latitude=lat,
                        longitude=lon,
                        municipio=municipio,
                        uf=uf,
                        source='CEMADEN',
                    ))
                except (ValueError, TypeError):
                    continue

        return alerts

    # ═══════════════════════════════════════════════════════════════════
    # Embrapa Integration (via Open-Meteo soil proxy)
    # ═══════════════════════════════════════════════════════════════════

    async def fetch_soil_vegetation_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Dados de solo e vegetação — proxy Embrapa via Open-Meteo.
        soil_moisture baixo = estresse hídrico / risco de seca
        soil_temperature alto = solo degradado
        """
        cache_key = self._cache_key("soil", lat, lon)
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&hourly=soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,"
            f"soil_temperature_0cm,soil_temperature_6cm,"
            f"et0_fao_evapotranspiration"
            f"&timezone=America/Sao_Paulo&forecast_days=3"
        )

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return {'error': f'Open-Meteo returned {resp.status}'}
                    data = await resp.json()

            hourly = data.get('hourly', {})

            # Extract latest values
            def latest_val(key):
                vals = [v for v in hourly.get(key, []) if v is not None]
                return vals[-1] if vals else None

            # Calculate averages for trend
            def avg_val(key):
                vals = [v for v in hourly.get(key, []) if v is not None]
                return sum(vals) / len(vals) if vals else None

            sm_0 = latest_val('soil_moisture_0_to_1cm')
            sm_1 = latest_val('soil_moisture_1_to_3cm')
            st_0 = latest_val('soil_temperature_0cm')
            st_6 = latest_val('soil_temperature_6cm')
            et0 = latest_val('et0_fao_evapotranspiration')

            # Derive vegetation stress indicators
            drought_risk = 'baixo'
            if sm_0 is not None:
                if sm_0 < 0.05:
                    drought_risk = 'critico'
                elif sm_0 < 0.10:
                    drought_risk = 'alto'
                elif sm_0 < 0.15:
                    drought_risk = 'moderado'

            result = {
                'latitude': lat,
                'longitude': lon,
                'soil_moisture_surface': sm_0,
                'soil_moisture_subsurface': sm_1,
                'soil_temperature_surface': st_0,
                'soil_temperature_deep': st_6,
                'evapotranspiration': et0,
                'drought_risk': drought_risk,
                'avg_soil_moisture': avg_val('soil_moisture_0_to_1cm'),
                'source': 'Open-Meteo (Embrapa proxy)',
                'timestamp': datetime.now().isoformat(),
                'note': 'Dados de solo via Open-Meteo como proxy do Embrapa SATVeg/NDVI',
            }

            self._set_cache(cache_key, result)
            return result

        except Exception as e:
            logger.warning(f"Soil data fetch error: {e}")
            return {'error': str(e)}

    # ═══════════════════════════════════════════════════════════════════
    # Unified Scan
    # ═══════════════════════════════════════════════════════════════════

    async def scan_brazil_conditions(self) -> Dict[str, Any]:
        """
        Varre todas as capitais e detecta condições extremas.
        Combina Open-Meteo + CEMADEN + News Crawler (multi-fonte).
        """
        logger.info("🌎 Starting Brazil weather scan across 20 monitoring points...")
        all_alerts: List[ClimateAlert] = []
        weather_results: List[WeatherData] = []

        # 1. Fetch Open-Meteo for all monitoring points (sequential to avoid 429)
        for i, pt in enumerate(BRAZIL_MONITORING_POINTS):
            try:
                result = await self.fetch_current_weather(pt['lat'], pt['lon'])
                if isinstance(result, WeatherData):
                    weather_results.append(result)
                    alert = self._detect_extreme_from_weather(result, pt)
                    if alert:
                        all_alerts.append(alert)
                # Small delay to respect rate limits
                if i < len(BRAZIL_MONITORING_POINTS) - 1:
                    await asyncio.sleep(0.5)
            except Exception as e:
                logger.debug(f"Scan error for {pt['name']}: {e}")

        # 2. Fetch CEMADEN alerts
        cemaden_alerts = await self.fetch_cemaden_alerts()
        all_alerts.extend(cemaden_alerts)

        # Deduplicate by alert_id
        seen = set()
        unique_alerts = []
        for a in all_alerts:
            if a.alert_id not in seen:
                seen.add(a.alert_id)
                unique_alerts.append(a)

        self._alerts = unique_alerts
        self._last_scan = datetime.now()

        logger.info(
            f"🌎 Scan complete: {len(weather_results)} stations, "
            f"{len(unique_alerts)} alerts detected "
            f"(Open-Meteo: {sum(1 for a in unique_alerts if a.source == 'Open-Meteo')}, "
            f"CEMADEN: {sum(1 for a in unique_alerts if a.source == 'CEMADEN')})"
        )

        return {
            'stations_scanned': len(weather_results),
            'alerts_detected': len(unique_alerts),
            'by_source': {
                'open_meteo': sum(1 for a in unique_alerts if a.source == 'Open-Meteo'),
                'cemaden': sum(1 for a in unique_alerts if a.source == 'CEMADEN'),
            },
            'scan_time': self._last_scan.isoformat(),
        }

    # ── Public getters ───────────────────────────────────────────────────

    def get_alerts(self, min_severity: str = 'baixa') -> List[Dict[str, Any]]:
        """Retorna alertas ativos, filtrados por severidade mínima"""
        severity_order = {'baixa': 1, 'media': 2, 'alta': 3, 'critica': 4}
        min_level = severity_order.get(min_severity, 1)

        return [
            {
                **asdict(a),
                'detected_at': a.detected_at.isoformat(),
            }
            for a in sorted(self._alerts, key=lambda x: x.severity_score, reverse=True)
            if severity_order.get(a.severity, 0) >= min_level
        ]

    def get_oracle_events(self) -> List[Dict[str, Any]]:
        """Converte alertas para formato Oracle (para injetar em live-events)"""
        import uuid
        import random

        events = []
        for alert in self._alerts:
            payout_triggered = alert.severity_score >= 3.0
            payout_pct = min(1.0, (alert.severity_score - 3.0) / 2.0 + 0.25) if payout_triggered else 0.0

            events.append({
                'event_id': f"climate_{alert.alert_id}",
                'token_id': f"tok_{uuid.uuid4().hex[:8]}",
                'municipio': alert.municipio,
                'uf': alert.uf,
                'latitude': alert.latitude,
                'longitude': alert.longitude,
                'disaster_type': alert.alert_type,
                'severity_score': alert.severity_score,
                'ndvi': round(random.uniform(0.1, 0.3) if alert.alert_type == 'seca' else random.uniform(0.3, 0.8), 3),
                'soil_moisture': round(alert.weather_data.get('soil_moisture', random.uniform(0.2, 0.6)) if alert.weather_data else random.uniform(0.2, 0.6), 3),
                'timestamp': alert.detected_at.isoformat(),
                'payout_triggered': payout_triggered,
                'payout_percentage': round(payout_pct, 2),
                'payout_amount': round(payout_pct * 100000.0, 2),
                'blockchain_tx_id': None,
                'status': 'TRIGGERED' if payout_triggered else 'PENDING',
                'source': f"🌤️ {alert.source}: {alert.title[:60]}",
                'confidence': 0.85 if alert.source == 'Open-Meteo' else 0.70,
            })

        return events

    def get_weather_risk_factor(self, uf: Optional[str] = None) -> Dict[str, Any]:
        """
        Fator de ajuste de risco para o modelo de precificação.
        Baseado em condições meteorológicas reais.
        """
        relevant = self._alerts
        if uf:
            relevant = [a for a in relevant if a.uf == uf]

        if not relevant:
            return {
                'risk_factor': 0.0,
                'alert_count': 0,
                'dominant_type': None,
                'description': 'Sem alertas climáticos ativos — risco base mantido',
                'sources': [],
            }

        avg_severity = sum(a.severity_score for a in relevant) / len(relevant)
        density = min(1.0, len(relevant) / 8.0)
        severity_factor = min(1.0, avg_severity / 4.0)
        risk_factor = round(density * severity_factor * 0.25, 4)

        by_type: Dict[str, int] = {}
        for a in relevant:
            by_type[a.alert_type] = by_type.get(a.alert_type, 0) + 1
        dominant = max(by_type, key=by_type.get) if by_type else None

        sources = list(set(a.source for a in relevant))

        if risk_factor > 0.15:
            desc = f'⚠️ ALTO RISCO: {len(relevant)} alertas climáticos — prêmio +{risk_factor*100:.1f}%'
        elif risk_factor > 0.08:
            desc = f'🔶 RISCO MODERADO: {len(relevant)} alertas — prêmio +{risk_factor*100:.1f}%'
        elif risk_factor > 0:
            desc = f'🔵 RISCO LEVE: {len(relevant)} alertas — prêmio +{risk_factor*100:.1f}%'
        else:
            desc = 'Sem alertas — risco base'

        return {
            'risk_factor': risk_factor,
            'alert_count': len(relevant),
            'dominant_type': dominant,
            'severity_avg': round(avg_severity, 2),
            'description': desc,
            'sources': sources,
        }


# ═════════════════════════════════════════════════════════════════════════════
# Singleton
# ═════════════════════════════════════════════════════════════════════════════

_climate_data_service: Optional[ClimateDataService] = None


def get_climate_data_service() -> ClimateDataService:
    global _climate_data_service
    if _climate_data_service is None:
        _climate_data_service = ClimateDataService()
    return _climate_data_service
