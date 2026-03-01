"""
Climate Oracle Service

Service for fetching and publishing climate data to Hathor blockchain.
Integrates with INMET, NOAA, and OpenMeteo for climate data.
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import hashlib
import json

import requests

from blockchain.hathor.hathor_service import HathorService, get_hathor_service

logger = logging.getLogger(__name__)


@dataclass
class ClimateDataPoint:
    """Single climate data point"""
    timestamp: datetime
    latitude: float
    longitude: float
    temperature_c: Optional[float] = None
    precipitation_mm: Optional[float] = None
    humidity_pct: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    pressure_hpa: Optional[float] = None
    source: str = ""
    quality: str = "verified"  # verified, provisional, estimated


@dataclass
class ClimateIndex:
    """Climate index calculation result"""
    index_type: str
    region: str
    latitude: float
    longitude: float
    start_date: datetime
    end_date: datetime
    value: float
    trigger_value: float
    trigger_condition: str
    trigger_met: bool
    data_points: List[ClimateDataPoint] = field(default_factory=list)
    calculation_method: str = ""


class ClimateOracleService:
    """
    Service for fetching and publishing climate data.
    
    Data Sources:
    - INMET (Brazilian National Institute of Meteorology)
    - NOAA (US National Oceanic and Atmospheric Administration)
    - OpenMeteo (Open-source weather API)
    
    Features:
    - Fetch historical climate data
    - Calculate climate indices
    - Publish data to Hathor blockchain
    - Verify data integrity
    - Redis caching for performance
    - Rate limiting for API compliance
    """
    
    def __init__(self, hathor_service: Optional[HathorService] = None, use_cache: bool = True):
        """
        Initialize Climate Oracle Service
        
        Args:
            hathor_service: Hathor service instance
            use_cache: Enable Redis caching (default: True)
        """
        self.hathor = hathor_service or get_hathor_service()
        
        # API endpoints
        self.inmet_base_url = "https://apitempo.inmet.gov.br"
        self.noaa_base_url = "https://www.ncei.noaa.gov/cdo-web/api/v2"
        self.openmeteo_base_url = "https://api.open-meteo.com/v1"
        
        # API keys (should be set in environment)
        self.noaa_token = "WDjhFaVSxFFpLelfYoKaQjnaTorOMcfV"  # NOAA API key
        
        # Redis cache configuration
        self.use_cache = use_cache
        self.redis_client = None
        self.cache_ttl = {
            "hourly": 3600,      # 1 hour for recent data
            "daily": 86400,      # 24 hours for historical data
            "weekly": 604800,    # 7 days for old data
        }
        
        # Rate limiting configuration
        self.rate_limits = {
            "noaa": {
                "requests_per_second": 5,
                "requests_per_day": 10000,
                "last_request_time": 0,
                "today_requests": 0,
                "today_date": datetime.now().date(),
            },
            "openmeteo": {
                "requests_per_second": 10,
                "requests_per_day": 100000,
                "last_request_time": 0,
                "today_requests": 0,
                "today_date": datetime.now().date(),
            },
        }
        
        # Data cache (in-memory fallback if Redis unavailable)
        self.data_cache: Dict[str, ClimateDataPoint] = {}
        self.index_cache: Dict[str, ClimateIndex] = {}
        
        # Initialize Redis if available
        self._initialize_redis()
        
        logger.info("ClimateOracleService initialized")
        if self.use_cache and self.redis_client:
            logger.info("Redis cache enabled")
        elif self.use_cache:
            logger.warning("Redis cache configured but not available, using in-memory cache")
    
    def _initialize_redis(self):
        """Initialize Redis connection if available"""
        if not self.use_cache:
            return
        
        try:
            import redis
            
            # Try to connect to Redis
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                password=os.getenv('REDIS_PASSWORD'),
                decode_responses=True,
                socket_connect_timeout=5,
            )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established")
            
        except ImportError:
            logger.warning("Redis package not installed, using in-memory cache")
            self.redis_client = None
        except Exception as e:
            logger.warning(f"Redis connection failed: {str(e)}, using in-memory cache")
            self.redis_client = None
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters"""
        key_data = f"{prefix}:{json.dumps(kwargs, sort_keys=True, default=str)}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.use_cache:
            return None
        
        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                # In-memory cache fallback
                return self.data_cache.get(key)
        except Exception as e:
            logger.debug(f"Cache get error: {str(e)}")
        
        return None
    
    def _cache_set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        if not self.use_cache:
            return
        
        try:
            if self.redis_client:
                self.redis_client.setex(key, ttl, json.dumps(value, default=str))
            else:
                # In-memory cache (no TTL, manual cleanup needed)
                self.data_cache[key] = value
        except Exception as e:
            logger.debug(f"Cache set error: {str(e)}")
    
    def _check_rate_limit(self, source: str) -> bool:
        """
        Check and enforce rate limiting
        
        Returns:
            True if request is allowed, False if rate limited
        """
        if source not in self.rate_limits:
            return True
        
        import time
        current_time = time.time()
        today = datetime.now().date()
        
        limit_config = self.rate_limits[source]
        
        # Reset daily counter if new day
        if today != limit_config["today_date"]:
            limit_config["today_requests"] = 0
            limit_config["today_date"] = today
        
        # Check daily limit
        if limit_config["today_requests"] >= limit_config["requests_per_day"]:
            logger.warning(f"Rate limit exceeded for {source}: daily limit reached")
            return False
        
        # Check per-second limit
        time_since_last = current_time - limit_config["last_request_time"]
        min_interval = 1.0 / limit_config["requests_per_second"]
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            logger.debug(f"Rate limiting {source}: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        # Update counters
        limit_config["last_request_time"] = time.time()
        limit_config["today_requests"] += 1
        
        return True
    
    def get_historical_data(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime,
        source: str = "openmeteo",
        use_cache: bool = True,
    ) -> List[ClimateDataPoint]:
        """
        Get historical climate data for a location and period
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            start_date: Start date
            end_date: End date
            source: Data source (inmet, noaa, openmeteo)
            use_cache: Use cached data if available
            
        Returns:
            List of ClimateDataPoint
        """
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(
                "historical_data",
                lat=latitude,
                lon=longitude,
                start=start_date.isoformat(),
                end=end_date.isoformat(),
                source=source,
            )
            
            cached_data = self._cache_get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {source} data")
                # Convert dict back to ClimateDataPoint objects
                return [
                    ClimateDataPoint(
                        timestamp=datetime.fromisoformat(p["timestamp"]),
                        latitude=p["latitude"],
                        longitude=p["longitude"],
                        temperature_c=p.get("temperature_c"),
                        precipitation_mm=p.get("precipitation_mm"),
                        humidity_pct=p.get("humidity_pct"),
                        wind_speed_kmh=p.get("wind_speed_kmh"),
                        wind_direction_deg=p.get("wind_direction_deg"),
                        pressure_hpa=p.get("pressure_hpa"),
                        source=p.get("source", source),
                        quality=p.get("quality", "verified"),
                    )
                    for p in cached_data
                ]
        
        # Check rate limit
        if not self._check_rate_limit(source):
            logger.error(f"Rate limit exceeded for {source}, using fallback")
            if source != "openmeteo":
                return self._get_openmeteo_data(latitude, longitude, start_date, end_date)
            return []
        
        # Fetch from source
        if source == "inmet":
            data_points = self._get_inmet_data(latitude, longitude, start_date, end_date)
        elif source == "noaa":
            data_points = self._get_noaa_data(latitude, longitude, start_date, end_date)
        else:
            data_points = self._get_openmeteo_data(latitude, longitude, start_date, end_date)
        
        # Cache the results
        if use_cache and data_points:
            # Determine TTL based on data age
            days_old = (datetime.now() - end_date).days
            if days_old <= 1:
                ttl = self.cache_ttl["hourly"]
            elif days_old <= 7:
                ttl = self.cache_ttl["daily"]
            else:
                ttl = self.cache_ttl["weekly"]
            
            # Convert to dict for JSON serialization
            cached_data = [
                {
                    "timestamp": p.timestamp.isoformat(),
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                    "temperature_c": p.temperature_c,
                    "precipitation_mm": p.precipitation_mm,
                    "humidity_pct": p.humidity_pct,
                    "wind_speed_kmh": p.wind_speed_kmh,
                    "wind_direction_deg": p.wind_direction_deg,
                    "pressure_hpa": p.pressure_hpa,
                    "source": p.source,
                    "quality": p.quality,
                }
                for p in data_points
            ]
            
            self._cache_set(cache_key, cached_data, ttl)
            logger.debug(f"Cached {len(data_points)} data points with TTL {ttl}s")
        
        return data_points
    
    def _get_openmeteo_data(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime,
    ) -> List[ClimateDataPoint]:
        """Fetch data from OpenMeteo API"""
        try:
            url = f"{self.openmeteo_base_url}/archive"
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "relative_humidity_2m_mean",
                    "wind_speed_10m_max",
                    "wind_direction_10m_dominant",
                    "surface_pressure",
                ],
                "timezone": "auto",
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            daily = data.get("daily", {})
            timestamps = daily.get("time", [])
            
            data_points = []
            for i, ts in enumerate(timestamps):
                point = ClimateDataPoint(
                    timestamp=datetime.strptime(ts, "%Y-%m-%d"),
                    latitude=latitude,
                    longitude=longitude,
                    temperature_c=self._safe_get(daily, "temperature_2m_max_mean", i),
                    precipitation_mm=self._safe_get(daily, "precipitation_sum", i),
                    humidity_pct=self._safe_get(daily, "relative_humidity_2m_mean", i),
                    wind_speed_kmh=self._safe_get(daily, "wind_speed_10m_max", i),
                    wind_direction_deg=self._safe_get(daily, "wind_direction_10m_dominant", i),
                    pressure_hpa=self._safe_get(daily, "surface_pressure", i),
                    source="openmeteo",
                )
                data_points.append(point)
            
            logger.info(f"Fetched {len(data_points)} data points from OpenMeteo")
            return data_points
            
        except Exception as e:
            logger.error(f"Failed to fetch OpenMeteo data: {str(e)}")
            raise
    
    def _get_inmet_data(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime,
    ) -> List[ClimateDataPoint]:
        """Fetch data from INMET API (Brazil)"""
        # INMET requires station code, so we'd need to find nearest station
        # This is a simplified implementation
        try:
            # Get stations
            stations_url = f"{self.inmet_base_url}/estacoes/T"
            response = requests.get(stations_url, timeout=30)
            response.raise_for_status()
            stations = response.json()
            
            # Find nearest station (simplified - would need proper distance calculation)
            # For now, use first station
            if not stations:
                raise ValueError("No INMET stations available")
            
            station = stations[0]
            station_code = station.get("CD_ESTACAO")
            
            # Get data for date range
            data_points = []
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                data_url = f"{self.inmet_base_url}/estacao/diaria/{station_code}/{date_str}"
                
                try:
                    response = requests.get(data_url, timeout=30)
                    if response.status_code == 200:
                        daily_data = response.json()
                        # Parse INMET response format
                        # (implementation depends on actual API response structure)
                        point = ClimateDataPoint(
                            timestamp=current_date,
                            latitude=latitude,
                            longitude=longitude,
                            source="inmet",
                        )
                        data_points.append(point)
                except Exception:
                    pass  # Skip days with no data
                
                current_date += timedelta(days=1)
            
            logger.info(f"Fetched {len(data_points)} data points from INMET")
            return data_points
            
        except Exception as e:
            logger.error(f"Failed to fetch INMET data: {str(e)}")
            # Fallback to OpenMeteo
            return self._get_openmeteo_data(latitude, longitude, start_date, end_date)
    
    def _get_noaa_data(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime,
    ) -> List[ClimateDataPoint]:
        """
        Fetch data from NOAA CDO Web Services v2 API
        
        API Documentation: https://www.ncei.noaa.gov/cdo-web/webservices/v2
        
        Rate Limits:
        - 5 requests/second
        - 10,000 requests/day
        
        Data Constraints:
        - Annual/Monthly data: max 10 years
        - Daily data: max 1 year
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of ClimateDataPoint
        """
        try:
            headers = {"token": self.noaa_token}
            base_url = self.noaa_base_url
            
            # Step 1: Find nearby stations within bounding box
            # Create bounding box (~50km radius)
            lat_range = 0.5  # ~55km
            lon_range = 0.5  # ~55km at equator, less at higher latitudes
            
            stations_url = f"{base_url}/stations"
            stations_params = {
                "limit": 10,  # Get up to 10 nearby stations
                "extent": f"{latitude-lat_range},{longitude-lon_range},{latitude+lat_range},{longitude+lon_range}",
            }
            
            logger.debug(f"Searching NOAA stations: {stations_params}")
            stations_response = requests.get(
                stations_url,
                headers=headers,
                params=stations_params,
                timeout=30
            )
            stations_response.raise_for_status()
            stations_data = stations_response.json()
            
            if not stations_data.get("results"):
                logger.warning(f"No NOAA stations found near ({latitude}, {longitude})")
                return self._get_openmeteo_data(latitude, longitude, start_date, end_date)
            
            # Step 2: Get data from first station
            station_id = stations_data["results"][0]["id"]
            logger.info(f"Using NOAA station: {station_id}")
            
            # Step 3: Fetch data for date range
            # Check date range constraints (max 1 year for daily data)
            date_range = (end_date - start_date).days
            if date_range > 365:
                logger.warning(f"Date range {date_range} days exceeds NOAA limit (365 days). Truncating.")
                end_date = start_date + timedelta(days=365)
            
            data_url = f"{base_url}/data"
            data_params = {
                "datasetid": "GHCND",  # Global Historical Climatology Network Daily
                "stationid": station_id,
                "startdate": start_date.strftime("%Y-%m-%d"),
                "enddate": end_date.strftime("%Y-%m-%d"),
                "units": "metric",  # Use metric units (°C, mm)
                "limit": 1000,  # Max allowed
                "includemetadata": "false",  # Faster response
            }
            
            logger.debug(f"Fetching NOAA data: {data_params}")
            data_response = requests.get(
                data_url,
                headers=headers,
                params=data_params,
                timeout=30
            )
            data_response.raise_for_status()
            data = data_response.json()
            
            # Step 4: Parse NOAA response
            # Group data by date
            data_by_date: Dict[str, Dict[str, float]] = {}
            
            for result in data.get("results", []):
                date_str = result.get("date", "")[:10]  # Extract YYYY-MM-DD
                datatype = result.get("datatype", "")
                value = result.get("value")
                
                if date_str not in data_by_date:
                    data_by_date[date_str] = {}
                
                # Map NOAA datatypes to our format
                if datatype == "TMAX":
                    data_by_date[date_str]["temperature_max"] = value / 10.0  # Convert from tenths of °C
                elif datatype == "TMIN":
                    data_by_date[date_str]["temperature_min"] = value / 10.0
                elif datatype == "TOBS":
                    data_by_date[date_str]["temperature_obs"] = value / 10.0
                elif datatype == "PRCP":
                    data_by_date[date_str]["precipitation"] = value / 10.0  # Convert from tenths of mm
                elif datatype == "SNOW":
                    data_by_date[date_str]["snowfall"] = value / 10.0
                elif datatype == "AWND":
                    data_by_date[date_str]["wind_speed"] = value / 10.0  # Convert from tenths of m/s
                elif datatype == "RHAV":
                    data_by_date[date_str]["humidity"] = value  # Already in %
            
            # Step 5: Convert to ClimateDataPoint objects
            data_points = []
            for date_str, values in data_by_date.items():
                try:
                    timestamp = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    timestamp = datetime.now()
                
                # Calculate average temperature if min/max available
                temperature = None
                if "temperature_max" in values and "temperature_min" in values:
                    temperature = (values["temperature_max"] + values["temperature_min"]) / 2.0
                elif "temperature_obs" in values:
                    temperature = values["temperature_obs"]
                
                point = ClimateDataPoint(
                    timestamp=timestamp,
                    latitude=latitude,
                    longitude=longitude,
                    temperature_c=temperature,
                    precipitation_mm=values.get("precipitation"),
                    humidity_pct=values.get("humidity"),
                    wind_speed_kmh=values.get("wind_speed", 0) * 3.6 if values.get("wind_speed") else None,  # Convert m/s to km/h
                    source="noaa",
                    quality="verified",
                )
                data_points.append(point)
            
            logger.info(f"Fetched {len(data_points)} data points from NOAA station {station_id}")
            return data_points
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("NOAA API authentication failed. Check API token.")
            elif e.response.status_code == 429:
                logger.error("NOAA API rate limit exceeded. Wait before retrying.")
            else:
                logger.error(f"NOAA API HTTP error: {str(e)}")
            return self._get_openmeteo_data(latitude, longitude, start_date, end_date)
            
        except Exception as e:
            logger.error(f"Failed to fetch NOAA data: {str(e)}")
            # Fallback to OpenMeteo
            return self._get_openmeteo_data(latitude, longitude, start_date, end_date)
    
    def _safe_get(self, data: Dict, key: str, index: int) -> Optional[float]:
        """Safely get value from list in dict"""
        value_list = data.get(key, [])
        if index < len(value_list):
            value = value_list[index]
            return None if value is None else float(value)
        return None
    
    def calculate_precipitation_index(
        self,
        data_points: List[ClimateDataPoint],
        aggregation: str = "sum",
    ) -> float:
        """
        Calculate precipitation index from data points
        
        Args:
            data_points: List of climate data points
            aggregation: Aggregation method (sum, avg, max, min)
            
        Returns:
            Calculated index value
        """
        if not data_points:
            return 0.0
        
        precipitation_values = [
            p.precipitation_mm for p in data_points
            if p.precipitation_mm is not None
        ]
        
        if not precipitation_values:
            return 0.0
        
        if aggregation == "sum":
            return sum(precipitation_values)
        elif aggregation == "avg":
            return sum(precipitation_values) / len(precipitation_values)
        elif aggregation == "max":
            return max(precipitation_values)
        elif aggregation == "min":
            return min(precipitation_values)
        else:
            return sum(precipitation_values)
    
    def calculate_temperature_index(
        self,
        data_points: List[ClimateDataPoint],
        aggregation: str = "avg",
    ) -> float:
        """
        Calculate temperature index from data points
        
        Args:
            data_points: List of climate data points
            aggregation: Aggregation method (avg, max, min)
            
        Returns:
            Calculated index value
        """
        if not data_points:
            return 0.0
        
        temperature_values = [
            p.temperature_c for p in data_points
            if p.temperature_c is not None
        ]
        
        if not temperature_values:
            return 0.0
        
        if aggregation == "avg":
            return sum(temperature_values) / len(temperature_values)
        elif aggregation == "max":
            return max(temperature_values)
        elif aggregation == "min":
            return min(temperature_values)
        else:
            return sum(temperature_values) / len(temperature_values)
    
    def check_trigger(
        self,
        index_value: float,
        trigger_value: float,
        condition: str,
    ) -> bool:
        """
        Check if index value meets trigger condition
        
        Args:
            index_value: Calculated index value
            trigger_value: Threshold value
            condition: "above" or "below"
            
        Returns:
            True if trigger condition is met
        """
        if condition == "above":
            return index_value >= trigger_value
        elif condition == "below":
            return index_value <= trigger_value
        else:
            raise ValueError(f"Unknown trigger condition: {condition}")
    
    def get_climate_index(
        self,
        index_type: str,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime,
        trigger_value: float,
        trigger_condition: str,
        source: str = "openmeteo",
    ) -> ClimateIndex:
        """
        Get complete climate index with trigger evaluation
        
        Args:
            index_type: Type of index (precipitation, temperature, etc.)
            latitude: Location latitude
            longitude: Location longitude
            start_date: Index start date
            end_date: Index end date
            trigger_value: Trigger threshold
            trigger_condition: "above" or "below"
            source: Data source
            
        Returns:
            ClimateIndex with calculation results
        """
        # Fetch data
        data_points = self.get_historical_data(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            source=source,
        )
        
        # Calculate index
        if index_type in ["precipitation", "drought", "flood"]:
            index_value = self.calculate_precipitation_index(data_points, "sum")
            calculation_method = "precipitation_sum"
        elif index_type in ["temperature", "heatwave", "frost"]:
            index_value = self.calculate_temperature_index(data_points, "avg")
            calculation_method = "temperature_avg"
        else:
            raise ValueError(f"Unknown index type: {index_type}")
        
        # Check trigger
        trigger_met = self.check_trigger(index_value, trigger_value, trigger_condition)
        
        # Create index object
        index = ClimateIndex(
            index_type=index_type,
            region=f"{latitude:.4f},{longitude:.4f}",
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            value=index_value,
            trigger_value=trigger_value,
            trigger_condition=trigger_condition,
            trigger_met=trigger_met,
            data_points=data_points,
            calculation_method=calculation_method,
        )
        
        # Cache result
        cache_key = f"{index_type}_{latitude}_{longitude}_{start_date}_{end_date}"
        self.index_cache[cache_key] = index
        
        logger.info(
            f"Climate index calculated: {index_type}={index_value}, "
            f"trigger={trigger_met}"
        )
        
        return index
    
    def publish_to_blockchain(
        self,
        index: ClimateIndex,
        data_hash: Optional[str] = None,
    ) -> str:
        """
        Publish climate index to Hathor blockchain
        
        Args:
            index: ClimateIndex to publish
            data_hash: Optional hash of raw data (for verification)
            
        Returns:
            Transaction hash
        """
        if not data_hash:
            # Calculate hash of index data
            data_string = f"{index.index_type}{index.value}{index.start_date}{index.end_date}"
            data_hash = hashlib.sha256(data_string.encode()).hexdigest()[:16]
        
        # Prepare data for blockchain
        # In production, this would use Nano Contracts
        # For now, we'll just log the publication
        
        publication_data = {
            "index_type": index.index_type,
            "region": index.region,
            "value": index.value,
            "trigger_value": index.trigger_value,
            "trigger_met": index.trigger_met,
            "start_date": index.start_date.isoformat(),
            "end_date": index.end_date.isoformat(),
            "data_hash": data_hash,
            "timestamp": datetime.now().isoformat(),
        }
        
        logger.info(f"Publishing climate index to blockchain: {publication_data}")
        
        # In production, would call:
        # result = self.hathor.execute_nano_contract(...)
        
        return data_hash
    
    def verify_data_integrity(
        self,
        index: ClimateIndex,
        expected_hash: str,
    ) -> bool:
        """
        Verify data integrity using hash
        
        Args:
            index: ClimateIndex to verify
            expected_hash: Expected hash value
            
        Returns:
            True if data integrity is verified
        """
        # Recalculate hash
        data_string = f"{index.index_type}{index.value}{index.start_date}{index.end_date}"
        calculated_hash = hashlib.sha256(data_string.encode()).hexdigest()[:16]
        
        is_valid = calculated_hash == expected_hash
        
        if not is_valid:
            logger.warning(f"Data integrity check failed: {index.index_type}")
        
        return is_valid
    
    def get_oracle_report(
        self,
        token_uid: str,
        index: ClimateIndex,
    ) -> Dict[str, Any]:
        """
        Generate oracle report for a climate token
        
        Args:
            token_uid: Token UID
            index: ClimateIndex result
            
        Returns:
            Oracle report dictionary
        """
        report = {
            "token_uid": token_uid,
            "oracle_type": "climate_index",
            "index_type": index.index_type,
            "region": index.region,
            "coordinates": {
                "latitude": index.latitude,
                "longitude": index.longitude,
            },
            "period": {
                "start": index.start_date.isoformat(),
                "end": index.end_date.isoformat(),
                "days": (index.end_date - index.start_date).days,
            },
            "result": {
                "index_value": index.value,
                "trigger_value": index.trigger_value,
                "trigger_condition": index.trigger_condition,
                "trigger_met": index.trigger_met,
            },
            "data_quality": {
                "data_points": len(index.data_points),
                "source": index.data_points[0].source if index.data_points else "unknown",
                "completeness": len(index.data_points) / max(1, (index.end_date - index.start_date).days),
            },
            "verification": {
                "timestamp": datetime.now().isoformat(),
                "oracle_signature": "signature_placeholder",
            },
        }
        
        logger.info(f"Oracle report generated for token {token_uid}")
        return report


# Singleton instance
climate_oracle_service = ClimateOracleService()


def get_climate_oracle_service() -> ClimateOracleService:
    """Get Climate Oracle Service instance"""
    return climate_oracle_service
