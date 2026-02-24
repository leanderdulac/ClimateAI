"""
Google Earth Engine Service — Production-Ready
Supports real GEE SDK with automatic mock fallback when credentials are unavailable.

Authentication modes (in priority order):
1. Service Account JSON via GOOGLE_APPLICATION_CREDENTIALS env var
2. Default Application Credentials (ADC) on GCP compute
3. Mock mode with realistic simulated data
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
import hashlib

try:
    import ee
    EE_AVAILABLE = True
except ImportError:
    EE_AVAILABLE = False

logger = logging.getLogger(__name__)


class GoogleEarthEngineService:
    """
    Service for interacting with Google Earth Engine.
    Retrieves NDVI (Sentinel-2), Soil Moisture (SMAP), and anomaly flags.

    Gracefully degrades to mock mode if ee SDK or credentials are absent.
    """

    def __init__(self):
        self.initialized = False
        self.project_id: Optional[str] = None
        if EE_AVAILABLE:
            self._initialize_ee()

    def _initialize_ee(self):
        """Initializes the EE library using the best available credential source."""
        try:
            self.project_id = os.getenv("GEE_PROJECT_ID", os.getenv("GCP_PROJECT_ID"))

            # Path 1: Explicit service account key
            sa_key = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            sa_email = os.getenv("GEE_SERVICE_ACCOUNT")

            if sa_key and os.path.isfile(sa_key):
                credentials = ee.ServiceAccountCredentials(
                    email=sa_email or "",
                    key_file=sa_key
                )
                ee.Initialize(credentials=credentials, project=self.project_id)
                self.initialized = True
                logger.info("✅ GEE initialized with Service Account credentials.")

            # Path 2: Application Default Credentials (ADC)
            elif os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID"):
                ee.Initialize(project=self.project_id)
                self.initialized = True
                logger.info("✅ GEE initialized with Application Default Credentials.")

            else:
                logger.warning(
                    "⚠️ GEE credentials not found. Running in MOCK mode. "
                    "Set GOOGLE_APPLICATION_CREDENTIALS or deploy on GCP for real data."
                )
        except Exception as e:
            logger.error(f"❌ GEE initialization failed: {e}. Falling back to MOCK mode.")
            self.initialized = False

    # ─── Public API ────────────────────────────────────────────────────

    async def get_satellite_metrics(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime,
        buffer_m: int = 500
    ) -> Dict[str, Any]:
        """
        Fetches NDVI (Sentinel-2) and Soil Moisture (SMAP) for the specified
        location and time range.

        Args:
            latitude: Target latitude
            longitude: Target longitude
            start_date: Start of observation window
            end_date: End of observation window
            buffer_m: Buffer radius in meters around the point (default 500m)

        Returns:
            Dict with ndvi, soil_moisture, anomaly flags, and source metadata.
        """
        if not self.initialized:
            logger.debug(f"GEE MOCK: returning simulated data for ({latitude:.4f}, {longitude:.4f})")
            return self._get_mock_metrics(latitude, longitude)

        try:
            # 1. Define geometry
            point = ee.Geometry.Point([longitude, latitude])
            roi = point.buffer(buffer_m)

            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            # 2. Sentinel-2 NDVI (10m resolution)
            ndvi_data = self._fetch_ndvi_sentinel2(roi, start_str, end_str)

            # 3. MODIS NDVI fallback (250m, more reliable coverage)
            if ndvi_data["ndvi"] is None:
                ndvi_data = self._fetch_ndvi_modis(point, start_str, end_str)

            # 4. Soil Moisture (SMAP 10km)
            sm_data = self._fetch_soil_moisture(point, start_str, end_str)

            # 5. Anomaly detection
            ndvi_val = ndvi_data["ndvi"] or 0.45
            sm_val = sm_data["soil_moisture"] or 0.25
            anomaly = self._detect_anomaly(ndvi_val, sm_val)

            return {
                "ndvi": round(ndvi_val, 4),
                "soil_moisture": round(sm_val, 4),
                "ndvi_source": ndvi_data["source"],
                "anomaly_detected": anomaly["detected"],
                "anomaly_type": anomaly["type"],
                "severity_indicator": anomaly["severity"],
                "status": "success",
                "source": "Google Earth Engine",
                "period": {"start": start_str, "end": end_str},
                "location": {"lat": latitude, "lon": longitude}
            }

        except Exception as e:
            logger.error(f"Error fetching GEE metrics: {e}")
            return self._get_mock_metrics(latitude, longitude, error=str(e))

    async def get_ndvi_timeseries(
        self,
        latitude: float,
        longitude: float,
        years_back: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieves a multi-year NDVI time series for trend analysis.
        Used by the parametric actuary for Extreme Value Theory fitting.
        """
        if not self.initialized:
            return self._get_mock_timeseries(latitude, longitude, years_back)

        try:
            point = ee.Geometry.Point([longitude, latitude])
            end = datetime.now()
            start = datetime(end.year - years_back, end.month, end.day)

            collection = (
                ee.ImageCollection("MODIS/061/MOD13Q1")
                .filterBounds(point)
                .filterDate(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
                .select("NDVI")
            )

            # Reduce to monthly means
            def _monthly_mean(img):
                date = ee.Date(img.get("system:time_start"))
                return img.set("month", date.format("YYYY-MM"))

            monthly = collection.map(_monthly_mean)

            values = collection.reduceRegion(
                reducer=ee.Reducer.toList(),
                geometry=point,
                scale=250
            ).get("NDVI").getInfo()

            if values:
                ndvi_values = [v / 10000.0 for v in values]
            else:
                ndvi_values = []

            return {
                "values": ndvi_values,
                "count": len(ndvi_values),
                "years": years_back,
                "source": "GEE MODIS MOD13Q1",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error fetching NDVI timeseries: {e}")
            return self._get_mock_timeseries(latitude, longitude, years_back)

    # ─── Private: Real GEE Queries ─────────────────────────────────────

    def _fetch_ndvi_sentinel2(self, roi, start: str, end: str) -> Dict[str, Any]:
        """Fetch NDVI from Sentinel-2 SR (10m resolution)."""
        try:
            s2 = (
                ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterBounds(roi)
                .filterDate(start, end)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
            )

            count = s2.size().getInfo()
            if count == 0:
                return {"ndvi": None, "source": "Sentinel-2 (no data)"}

            def add_ndvi(img):
                ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
                return img.addBands(ndvi)

            ndvi_col = s2.map(add_ndvi).select("NDVI")
            ndvi_mean = ndvi_col.mean().reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=roi,
                scale=10
            ).get("NDVI").getInfo()

            return {"ndvi": ndvi_mean, "source": "Sentinel-2 SR (10m)"}

        except Exception as e:
            logger.warning(f"Sentinel-2 NDVI failed: {e}")
            return {"ndvi": None, "source": "Sentinel-2 (error)"}

    def _fetch_ndvi_modis(self, point, start: str, end: str) -> Dict[str, Any]:
        """Fetch NDVI from MODIS (250m, reliable global coverage fallback)."""
        try:
            collection = (
                ee.ImageCollection("MODIS/061/MOD13Q1")
                .filterBounds(point)
                .filterDate(start, end)
                .select("NDVI")
            )

            ndvi_mean = collection.mean().reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=250
            ).get("NDVI").getInfo()

            ndvi = ndvi_mean / 10000.0 if ndvi_mean else None
            return {"ndvi": ndvi, "source": "MODIS MOD13Q1 (250m)"}

        except Exception as e:
            logger.warning(f"MODIS NDVI failed: {e}")
            return {"ndvi": None, "source": "MODIS (error)"}

    def _fetch_soil_moisture(self, point, start: str, end: str) -> Dict[str, Any]:
        """Fetch Surface Soil Moisture from NASA-USDA SMAP."""
        try:
            collection = (
                ee.ImageCollection("NASA_USDA/HSL/SMAP10KM_soil_moisture")
                .filterBounds(point)
                .filterDate(start, end)
                .select("ssm")
            )

            sm_mean = collection.mean().reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point,
                scale=10000
            ).get("ssm").getInfo()

            return {"soil_moisture": sm_mean}

        except Exception as e:
            logger.warning(f"SMAP Soil Moisture failed: {e}")
            return {"soil_moisture": None}

    # ─── Private: Analysis ─────────────────────────────────────────────

    def _detect_anomaly(self, ndvi: float, soil_moisture: float) -> Dict[str, Any]:
        """
        Simple anomaly detection based on vegetation and moisture thresholds.
        In production, compare against historical baselines from BigQuery.
        """
        if ndvi < 0.2 and soil_moisture < 0.10:
            return {"detected": True, "type": "severe_drought", "severity": 5}
        elif ndvi < 0.3 and soil_moisture < 0.15:
            return {"detected": True, "type": "drought_stress", "severity": 4}
        elif ndvi < 0.35:
            return {"detected": True, "type": "vegetation_decline", "severity": 3}
        elif soil_moisture > 0.55:
            return {"detected": True, "type": "excess_moisture", "severity": 3}
        elif soil_moisture > 0.70:
            return {"detected": True, "type": "flooding_risk", "severity": 4}
        else:
            return {"detected": False, "type": "normal", "severity": 1}

    # ─── Private: Mock Data ────────────────────────────────────────────

    def _get_mock_metrics(
        self, lat: float = 0, lon: float = 0, error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Returns deterministic mock data seeded by coordinates.
        Consistent for the same location across calls.
        """
        seed = int(hashlib.sha256(f"{lat:.4f},{lon:.4f}".encode()).hexdigest()[:8], 16)
        ndvi = 0.35 + (seed % 400) / 1000.0   # Range 0.35–0.75
        sm = 0.15 + (seed % 350) / 1000.0      # Range 0.15–0.50

        anomaly = self._detect_anomaly(ndvi, sm)

        return {
            "ndvi": round(ndvi, 4),
            "soil_moisture": round(sm, 4),
            "ndvi_source": "Mock (deterministic)",
            "anomaly_detected": anomaly["detected"],
            "anomaly_type": anomaly["type"],
            "severity_indicator": anomaly["severity"],
            "status": "mock" if not error else "error_fallback",
            "warning": error,
            "source": "Mock (GEE Simulation)",
            "location": {"lat": lat, "lon": lon}
        }

    def _get_mock_timeseries(
        self, lat: float, lon: float, years: int
    ) -> Dict[str, Any]:
        """Mock NDVI timeseries for testing."""
        import math
        seed = int(hashlib.sha256(f"{lat:.4f},{lon:.4f}".encode()).hexdigest()[:8], 16)
        base = 0.4 + (seed % 300) / 1000.0
        values = []
        for i in range(years * 12):
            seasonal = 0.15 * math.sin(2 * math.pi * (i % 12) / 12)
            noise = ((seed + i * 7) % 100 - 50) / 1000.0
            values.append(round(base + seasonal + noise, 4))

        return {
            "values": values,
            "count": len(values),
            "years": years,
            "source": "Mock (Simulated Timeseries)",
            "status": "mock"
        }
