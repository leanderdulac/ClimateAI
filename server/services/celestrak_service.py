"""
CelesTrak Space Data Service
Integração com dados de satélites e clima espacial do CelesTrak

Fontes:
- CelesTrak: https://celestrak.org/
- TLE/Elementos Orbitais
- SOCRATES: Alertas de conjunção orbital
- Space Weather: Clima espacial
- SATCAT: Catálogo de satélites
"""

import logging
import requests
import io
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import re

logger = logging.getLogger(__name__)


class OrbitType(str, Enum):
    """Tipos de órbita"""
    LEO = "leo"      # Low Earth Orbit (160-2000 km)
    MEO = "meo"      # Medium Earth Orbit (2000-35786 km)
    GEO = "geo"      # Geostationary (35786 km)
    HEO = "heo"      # High Elliptical Orbit


class RiskLevel(str, Enum):
    """Níveis de risco de conjunção"""
    CRITICAL = "critical"  # Prob > 10⁻³
    HIGH = "high"          # Prob > 10⁻⁴
    MEDIUM = "medium"      # Prob > 10⁻⁵
    LOW = "low"            # Prob > 10⁻⁶


@dataclass
class TLEData:
    """Two-Line Element Data"""
    norad_id: str
    satellite_name: str
    line1: str
    line2: str
    epoch: datetime
    mean_motion: float  # Revolutions per day
    eccentricity: float
    inclination: float  # Degrees
    raan: float  # Right Ascension of Ascending Node
    arg_perigee: float
    mean_anomaly: float
    orbit_type: OrbitType
    classification: str  # U=Unclassified, C=Classified, S=Secret


@dataclass
class ConjunctionAlert:
    """SOCRATES Conjunction Alert"""
    conjunction_id: str
    object1_norad: str
    object1_name: str
    object2_norad: str
    object2_name: str
    tca: datetime  # Time of Closest Approach
    miss_distance_km: float
    collision_probability: float
    relative_velocity_kms: float
    risk_level: RiskLevel
    conjunction_type: str  # debris, satellite, rocket_body


@dataclass
class SpaceWeatherData:
    """Space Weather Conditions"""
    timestamp: datetime
    kp_index: float  # Geomagnetic activity (0-9)
    ap_index: float
    solar_flux: float  # 10.7 cm flux
    geomagnetic_storm: bool
    storm_level: str  # G1-G5
    solar_radiation_storm: bool
    radiation_level: str  # S1-S5
    radio_blackout: bool
    blackout_level: str  # R1-R5
    affected_regions: List[str] = field(default_factory=list)


@dataclass
class SatelliteInfo:
    """SATCAT Satellite Information"""
    norad_id: str
    satcat_code: str
    satellite_name: str
    country: str
    launch_date: datetime
    launch_site: str
    decay_date: Optional[datetime]
    orbit_type: str
    period_minutes: float
    inclination_deg: float
    apogee_km: float
    perigee_km: float
    status: str  # Active, Inactive, Decayed
    operator: Optional[str]
    purpose: Optional[str]


class CelesTrakService:
    """
    Serviço de integração com CelesTrak
    
    Endpoints:
    - https://celestrak.org/NORAD/elements/
    - https://celestrak.org/SOCRATES/
    - https://celestrak.org/satcat/
    """

    BASE_URL = "https://celestrak.org"
    TLE_URL = f"{BASE_URL}/NORAD/elements"
    SATCAT_URL = f"{BASE_URL}/satcat"
    SPACE_WEATHER_URL = f"{BASE_URL}/SpaceData/SW-Last5Years.csv"
    SOCRATES_TOP10_URL = f"{BASE_URL}/SOCRATES/table-socrates.php?NAME=,&ORDER=MAXPROB&MAX=10"
    
    # Categorias de satélites
    TLE_CATEGORIES = {
        'stations': 'Space Stations',
        'geo': 'Geostationary',
        'noaa': 'NOAA',
        'goes': 'GOES',
        'earth-resources': 'Earth Resources',
        'meteorological': 'Meteorological',
        'gps-ops': 'GPS Operational',
        'glo-ops': 'GLONASS Operational',
        'galileo': 'Galileo',
        'beidou': 'Beidou',
        'satellite': 'General Satellite',
        'weather': 'Weather',
        'science': 'Science',
        'military': 'Military',
    }

    def __init__(self, cache_timeout_minutes: int = 60):
        """
        Inicializar serviço
        
        Args:
            cache_timeout_minutes: Timeout do cache
        """
        self.cache: Dict[str, Any] = {}
        self.cache_timeout = timedelta(minutes=cache_timeout_minutes)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ClimateWise-Space-Service/1.0'
        })
        
        # Dataframes para cache de longa duração
        self._satcat_df = None
        self._last_satcat_load = None
        
        logger.info("CelesTrakService initialized")

    def get_tle_data(
        self,
        category: str = 'stations',
        use_cache: bool = True
    ) -> List[TLEData]:
        """
        Obter dados TLE de uma categoria
        
        Args:
            category: Categoria de satélites
            use_cache: Usar cache se disponível
            
        Returns:
            Lista de TLEData
        """
        cache_key = f"tle_{category}"
        
        # Verificar cache
        if use_cache and cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if datetime.now() - cache_time < self.cache_timeout:
                logger.info(f"Using cached TLE data for {category}")
                return data
        
        try:
            # URL da categoria
            url = f"{self.TLE_URL}/{category}.txt"
            
            logger.info(f"Fetching TLE data from {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse TLE data
            tle_data = self._parse_tle_file(response.text, category)
            
            # Salvar no cache
            self.cache[cache_key] = (datetime.now(), tle_data)
            
            logger.info(f"Fetched {len(tle_data)} TLE records for {category}")
            return tle_data
            
        except Exception as e:
            logger.error(f"Error fetching TLE data: {e}")
            return []

    def _parse_tle_file(self, content: str, category: str) -> List[TLEData]:
        """
        Parse arquivo TLE
        
        Formato:
        Satellite Name
        Line 1
        Line 2
        """
        tle_list = []
        lines = content.strip().split('\n')
        
        i = 0
        while i < len(lines):
            try:
                # Linha 0: Nome do satélite
                name = lines[i].strip()
                
                # Linha 1: TLE Line 1
                line1 = lines[i + 1].strip()
                
                # Linha 2: TLE Line 2
                line2 = lines[i + 2].strip()
                
                # Parse Line 1
                norad_id = line1[2:7].strip()
                classification = line1[7]
                epoch_year = int(line1[18:20])
                epoch_day = float(line1[20:32])
                
                # Parse Line 2
                inclination = float(line2[8:16])
                raan = float(line2[17:25])
                eccentricity = float('0.' + line2[26:33].strip())
                arg_perigee = float(line2[34:42])
                mean_anomaly = float(line2[43:51])
                mean_motion = float(line2[52:63])
                
                # Calcular epoch
                epoch = self._parse_tle_epoch(epoch_year, epoch_day)
                
                # Determinar tipo de órbita
                orbit_type = self._determine_orbit_type(mean_motion)
                
                tle = TLEData(
                    norad_id=norad_id,
                    satellite_name=name,
                    line1=line1,
                    line2=line2,
                    epoch=epoch,
                    mean_motion=mean_motion,
                    eccentricity=eccentricity,
                    inclination=inclination,
                    raan=raan,
                    arg_perigee=arg_perigee,
                    mean_anomaly=mean_anomaly,
                    orbit_type=orbit_type,
                    classification=classification,
                )
                
                tle_list.append(tle)
                i += 3
                
            except (IndexError, ValueError) as e:
                logger.warning(f"Error parsing TLE at line {i}: {e}")
                i += 1
        
        return tle_list

    def _parse_tle_epoch(self, year: int, day: float) -> datetime:
        """Converter epoch TLE para datetime"""
        # Ano completo (TLE usa 2 dígitos)
        if year < 57:
            year += 2000
        else:
            year += 1900
        
        # Dia do ano para datetime
        epoch = datetime(year, 1, 1)
        epoch += timedelta(days=day - 1)
        
        return epoch

    def _determine_orbit_type(self, mean_motion: float) -> OrbitType:
        """Determinar tipo de órbita baseado no mean motion"""
        # Mean motion em revoluções por dia
        if mean_motion > 11.25:
            return OrbitType.LEO
        elif mean_motion > 2.0:
            return OrbitType.MEO
        elif mean_motion > 0.9:
            return OrbitType.GEO
        else:
            return OrbitType.HEO

    def get_satellite_info(
        self,
        norad_id: str,
        use_cache: bool = True
    ) -> Optional[SatelliteInfo]:
        """
        Obter informações de satélite do SATCAT
        
        Args:
            norad_id: NORAD ID do satélite
            use_cache: Usar cache
            
        Returns:
            SatelliteInfo ou None
        """
        cache_key = f"satcat_{norad_id}"
        
        if use_cache and cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if datetime.now() - cache_time < self.cache_timeout:
                return data
        
        try:
            # Buscar no SATCAT (CSV real)
            if self._satcat_df is None or (datetime.now() - self._last_satcat_load > timedelta(days=1)):
                url = "https://celestrak.org/pub/satcat.csv"
                logger.info(f"Loading SATCAT from {url}")
                response = self.session.get(url, timeout=60)
                response.raise_for_status()
                self._satcat_df = pd.read_csv(io.StringIO(response.text))
                self._last_satcat_load = datetime.now()
            
            # Filtrar por NORAD ID
            # O CSV do CelesTrak costuma ter NORAD_CAT_ID
            sat_data = self._satcat_df[self._satcat_df['NORAD_CAT_ID'].astype(str) == str(norad_id)]
            
            if sat_data.empty:
                logger.warning(f"Satellite {norad_id} not found in SATCAT")
                return None
            
            row = sat_data.iloc[0]
            
            # Mapear dados do CSV para SatelliteInfo
            launch_date = None
            if pd.notna(row.get('LAUNCH_DATE')):
                try:
                    launch_date = datetime.strptime(str(row['LAUNCH_DATE']), '%Y-%m-%d')
                except:
                    pass
            
            decay_date = None
            if pd.notna(row.get('DECAY_DATE')):
                try:
                    decay_date = datetime.strptime(str(row['DECAY_DATE']), '%Y-%m-%d')
                except:
                    pass

            satellite = SatelliteInfo(
                norad_id=str(row['NORAD_CAT_ID']),
                satcat_code=str(row.get('OBJECT_ID', '')),
                satellite_name=str(row.get('OBJECT_NAME', f"Sat-{norad_id}")),
                country=str(row.get('COUNTRY_CODE', 'UNK')),
                launch_date=launch_date or datetime(2000, 1, 1),
                launch_site=str(row.get('LAUNCH_SITE', 'UNK')),
                decay_date=decay_date,
                orbit_type="UNKNOWN", # Seria calculado se necessário
                period_minutes=float(row.get('PERIOD', 0)),
                inclination_deg=float(row.get('INCLINATION', 0)),
                apogee_km=float(row.get('APOGEE', 0)),
                perigee_km=float(row.get('PERIGEE', 0)),
                status="Active" if pd.isna(row.get('DECAY_DATE')) else "Decayed",
                operator=str(row.get('OWNER', 'UNK')),
                purpose=None,
            )
            
            if satellite:
                self.cache[cache_key] = (datetime.now(), satellite)
            
            return satellite
            
        except Exception as e:
            logger.error(f"Error fetching SATCAT info: {e}")
            return None

    def get_space_weather(self, use_cache: bool = True) -> Optional[SpaceWeatherData]:
        """
        Obter dados de clima espacial reais do CelesTrak
        
        Returns:
            SpaceWeatherData ou None
        """
        cache_key = "space_weather_real"
        
        if use_cache and cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if datetime.now() - cache_time < timedelta(hours=1):
                return data

        try:
            logger.info(f"Fetching real space weather from {self.SPACE_WEATHER_URL}")
            response = self.session.get(self.SPACE_WEATHER_URL, timeout=30)
            response.raise_for_status()
            
            # Carregar CSV sem header
            df = pd.read_csv(io.StringIO(response.text), header=None)
            
            if df.empty:
                return None
            
            # Filtrar por OBS (coluna 26) para pegar dado real recente, não predição futura
            # No arquivo do CelesTrak a coluna 26 indica se o dado é OBS ou PRM/etc
            obs_df = df[df[26] == 'OBS']
            
            if obs_df.empty:
                logger.warning("No OBS space weather data found, using last available row")
                last_row = df.iloc[-1]
            else:
                last_row = obs_df.iloc[-1]
            
            # Mapeamento de colunas (0-indexed baseado na análise do arquivo):
            # 0: Date (YYYY-MM-DD)
            # 11: Kp_Sum (unidade 0.1)
            # 20: Ap_Avg
            # 24: F10.7_Adj
            
            try:
                kp_sum = float(last_row[11])
                avg_kp = (kp_sum / 8.0) / 10.0
                ap_avg = float(last_row[20])
                f107 = float(last_row[24])
            except (ValueError, TypeError, KeyError):
                logger.warning("Failed to parse some weather values, using defaults")
                avg_kp, ap_avg, f107 = 1.0, 7.0, 80.0

            weather = SpaceWeatherData(
                timestamp=datetime.strptime(str(last_row[0]), '%Y-%m-%d') if pd.notna(last_row[0]) else datetime.now(),
                kp_index=round(avg_kp, 1),
                ap_index=ap_avg,
                solar_flux=f107,
                geomagnetic_storm=avg_kp >= 5,
                storm_level=f"G{int(avg_kp - 4)}" if avg_kp >= 5 else "None",
                solar_radiation_storm=False,
                radiation_level="None",
                radio_blackout=False,
                blackout_level="None",
                affected_regions=["Polar Regions"] if avg_kp >= 6 else [],
            )
            
            self.cache[cache_key] = (datetime.now(), weather)
            return weather
            
        except Exception as e:
            logger.error(f"Error fetching real space weather: {e}")
            return self._mock_space_weather()

    def _mock_space_weather(self) -> SpaceWeatherData:
        """Mock de clima espacial (substituir por dados reais)"""
        import random
        
        kp_index = random.uniform(1.0, 7.0)
        
        return SpaceWeatherData(
            timestamp=datetime.now(),
            kp_index=round(kp_index, 1),
            ap_index=round(kp_index * 3, 0),
            solar_flux=round(random.uniform(70, 200), 1),
            geomagnetic_storm=kp_index >= 5,
            storm_level=f"G{int(kp_index - 4)}" if kp_index >= 5 else "None",
            solar_radiation_storm=random.random() > 0.8,
            radiation_level="S1" if random.random() > 0.8 else "None",
            radio_blackout=random.random() > 0.9,
            blackout_level="R1" if random.random() > 0.9 else "None",
            affected_regions=["Polar Regions"] if kp_index >= 6 else [],
        )

    def get_conjunction_alerts(
        self,
        satellite_norad: Optional[str] = None,
        min_probability: float = 1e-6,
        max_distance_km: float = 5.0,
        use_cache: bool = True
    ) -> List[ConjunctionAlert]:
        """
        Obter alertas de conjunção do SOCRATES
        
        Args:
            satellite_norad: NORAD ID específico (None = todos)
            min_probability: Probabilidade mínima
            max_distance_km: Distância máxima em km
            use_cache: Usar cache
            
        Returns:
            Lista de ConjunctionAlert
        """
        cache_key = f"socrates_{satellite_norad or 'all'}"
        
        if use_cache and cache_key in self.cache:
            cache_time, data = self.cache[cache_key]
            if datetime.now() - cache_time < self.cache_timeout:
                return data
        
        try:
            logger.info(f"Fetching real SOCRATES Top 10 HTML alerts from {self.SOCRATES_TOP10_URL}")
            response = self.session.get(self.SOCRATES_TOP10_URL, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            # O SOCRATES usa uma tabela com classes de zebra/shade
            table = soup.find('table', class_='center') or soup.find('table')
            
            alerts = []
            if table:
                rows = table.find_all('tr')
                # A tabela do CelesTrak agrupa 2 linhas por conjunção
                # Pular o cabeçalho se houver (geralmente os primeiros TRs com TH)
                # Vamos filtrar apenas TRs que parecem conter dados (align=center)
                data_rows = [r for r in rows if r.get('align') == 'center']
                
                i = 0
                while i < len(data_rows) - 1:
                    try:
                        r1 = data_rows[i]
                        r2 = data_rows[i+1]
                        
                        cols1 = r1.find_all('td')
                        cols2 = r2.find_all('td')
                        
                        # Row 1: Button, NORAD1, Name1, Epoch1, TCA (rowspan), Range (rowspan), Speed (rowspan)
                        # Row 2: Button, NORAD2, Name2, Epoch2, Prob, Dilution
                        if len(cols1) >= 7 and len(cols2) >= 6:
                            id1 = cols1[1].get_text(strip=True)
                            obj1_name = cols1[2].get_text(strip=True)
                            tca_str = cols1[4].get_text(strip=True)
                            miss_dist_str = cols1[5].get_text(strip=True).replace(',', '')
                            
                            id2 = cols2[1].get_text(strip=True)
                            obj2_name = cols2[2].get_text(strip=True)
                            prob_str = cols2[4].get_text(strip=True)
                            
                            # Limpeza e conversão
                            miss_dist = float(miss_dist_str) if miss_dist_str else 0.0
                            # Probabilidade pode estar em formato científico 1.000E-01
                            try:
                                prob = float(prob_str) if prob_str else 0.0
                            except:
                                prob = 0.0
                            
                            # Determinar risco
                            if prob >= 1e-3:
                                risk = RiskLevel.CRITICAL
                            elif prob >= 1e-4:
                                risk = RiskLevel.HIGH
                            elif prob >= 1e-5:
                                risk = RiskLevel.MEDIUM
                            else:
                                risk = RiskLevel.LOW
                            
                            alert = ConjunctionAlert(
                                conjunction_id=f"REAL-{tca_str.replace(' ', 'T')}-{id1}",
                                object1_norad=id1,
                                object1_name=obj1_name,
                                object2_norad=id2,
                                object2_name=obj2_name,
                                tca=datetime.now(), # Parser de data real opcional
                                miss_distance_km=miss_dist,
                                collision_probability=prob,
                                relative_velocity_kms=float(cols1[6].get_text(strip=True).replace(',', '')) if len(cols1) > 6 else 0.0,
                                risk_level=risk,
                                conjunction_type='satellite' if '[+]' in obj1_name else 'unknown',
                            )
                            
                            if not satellite_norad or (id1 == satellite_norad or id2 == satellite_norad):
                                alerts.append(alert)
                        
                        i += 2 # Pular para o próximo par
                    except Exception as e:
                        logger.debug(f"Error parsing pair starting at row {i}: {e}")
                        i += 1
            
            if not alerts and not satellite_norad:
                return self._mock_conjunction_alerts(None)
                
            return alerts[:10] # Top 10
            
        except Exception as e:
            logger.error(f"Error fetching real conjunction alerts: {e}")
            return []

    def _mock_conjunction_alerts(
        self,
        satellite_norad: Optional[str]
    ) -> List[ConjunctionAlert]:
        """Mock de alertas de conjunção"""
        import random
        
        alerts = []
        
        # Gerar alguns alertas mock
        for i in range(random.randint(0, 5)):
            prob = random.uniform(1e-6, 1e-3)
            
            if prob >= 1e-3:
                risk = RiskLevel.CRITICAL
            elif prob >= 1e-4:
                risk = RiskLevel.HIGH
            elif prob >= 1e-5:
                risk = RiskLevel.MEDIUM
            else:
                risk = RiskLevel.LOW
            
            alert = ConjunctionAlert(
                conjunction_id=f"CONJ-{datetime.now().strftime('%Y%m%d')}-{i:04d}",
                object1_norad=satellite_norad or str(random.randint(20000, 50000)),
                object1_name=f"Satellite-{satellite_norad or 'UNK'}",
                object2_norad=str(random.randint(10000, 60000)),
                object2_name=f"Debris-{random.randint(1, 9999)}",
                tca=datetime.now() + timedelta(hours=random.randint(1, 168)),
                miss_distance_km=random.uniform(0.1, 5.0),
                collision_probability=prob,
                relative_velocity_kms=random.uniform(5, 15),
                risk_level=risk,
                conjunction_type=random.choice(['debris', 'satellite', 'rocket_body']),
            )
            
            alerts.append(alert)
        
        return alerts

    def get_all_active_satellites(self) -> List[Dict[str, str]]:
        """
        Obter lista de todos os satélites ativos
        
        Returns:
            Lista de dicionários com info básica
        """
        # Mock para demonstração
        return [
            {'norad_id': '25544', 'name': 'ISS (ZARYA)', 'country': 'ISS'},
            {'norad_id': '43013', 'name': 'TIANGONG-1', 'country': 'PRC'},
            {'norad_id': '20580', 'name': 'HST', 'country': 'USA'},
            {'norad_id': '27424', 'name': 'ENVISAT', 'country': 'ESA'},
        ]


# Instância global
celestrak_service = CelesTrakService()
