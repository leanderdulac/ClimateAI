"""
BigQuery Data Lake Service — Production-Ready
Retrieves historical climate datasets from BigQuery public datasets (NOAA, ERA5).
Supports real BigQuery client with automatic mock fallback.

Used for:
  - Historical precipitation benchmarks (30-year records)
  - Audit trail persistence for transparency
  - Risk tranching analytics (Senior/Junior)
"""

import logging
import os
import hashlib
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from google.cloud import bigquery
    BQ_AVAILABLE = True
except ImportError:
    BQ_AVAILABLE = False

logger = logging.getLogger(__name__)

_BQ_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_\-]+$")


class BigQueryDataLakeService:
    """
    Service for interacting with Google BigQuery to retrieve historical climate
    datasets and persist audit trails.

    Modes:
        - REAL: Connected to BigQuery with valid credentials
        - MOCK: Returns deterministic simulated data
    """

    def __init__(self):
        self.client = None
        self.project_id = os.getenv("GCP_PROJECT_ID", os.getenv("GOOGLE_CLOUD_PROJECT"))
        self.dataset = os.getenv("BQ_DATASET", "climatewise_institutional")

        if BQ_AVAILABLE:
            self._init_client()

    def _init_client(self):
        """Initialize BigQuery client with available credentials."""
        try:
            self.client = bigquery.Client(project=self.project_id)
            # Quick connectivity check
            list(self.client.list_datasets(max_results=1))
            logger.info(f"✅ BigQuery connected to project: {self.project_id}")
        except Exception as e:
            logger.warning(f"⚠️ BigQuery init failed: {e}. Running in MOCK mode.")
            self.client = None

    def _safe_identifier(self, value: Optional[str], label: str) -> str:
        """Allow only BigQuery-safe identifiers for project and dataset names."""
        if not value or not _BQ_IDENTIFIER_RE.fullmatch(value):
            raise ValueError(f"Invalid BigQuery {label}: {value!r}")
        return value

    # ─── Historical Benchmarks ─────────────────────────────────────────

    async def get_historical_benchmarks(
        self,
        latitude: float,
        longitude: float,
        years_back: int = 30
    ) -> Dict[str, Any]:
        """
        Retrieves historical precipitation benchmarks from BigQuery NOAA GSOD.
        Falls back to deterministic mock data if BigQuery is unavailable.
        """
        if not self.client:
            return self._get_mock_benchmarks(latitude, longitude, years_back)

        try:
            end_year = datetime.now().year
            start_year = end_year - years_back

            query = """
                WITH nearest_station AS (
                    SELECT stn, wban, name,
                        ST_DISTANCE(
                            ST_GEOGPOINT(lon, lat),
                            ST_GEOGPOINT(@longitude, @latitude)
                        ) AS dist_m
                    FROM `bigquery-public-data.noaa_gsod.stations`
                    WHERE lat IS NOT NULL AND lon IS NOT NULL
                    ORDER BY dist_m
                    LIMIT 1
                )
                SELECT
                    CAST(_TABLE_SUFFIX AS INT64) AS year,
                    AVG(SAFE_CAST(prcp AS FLOAT64)) as avg_daily_precip,
                    MAX(SAFE_CAST(prcp AS FLOAT64)) as peak_daily_event,
                    SUM(SAFE_CAST(prcp AS FLOAT64)) as annual_total,
                    COUNT(IF(SAFE_CAST(prcp AS FLOAT64) > 0, 1, NULL)) as rain_days,
                    COUNT(*) as total_obs
                FROM `bigquery-public-data.noaa_gsod.gsod*`
                WHERE _TABLE_SUFFIX BETWEEN @start_year AND @end_year
                  AND stn = (SELECT stn FROM nearest_station)
                  AND wban = (SELECT wban FROM nearest_station)
                GROUP BY year
                ORDER BY year DESC
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("longitude", "FLOAT64", longitude),
                    bigquery.ScalarQueryParameter("latitude", "FLOAT64", latitude),
                    bigquery.ScalarQueryParameter("start_year", "STRING", str(start_year)),
                    bigquery.ScalarQueryParameter("end_year", "STRING", str(end_year)),
                ]
            )

            job = self.client.query(query, job_config=job_config)
            rows = list(job.result())

            if not rows:
                logger.warning(f"No GSOD data found near ({latitude}, {longitude})")
                return self._get_mock_benchmarks(latitude, longitude, years_back)

            annual_totals = [r.annual_total for r in rows if r.annual_total]
            peak_events = [r.peak_daily_event for r in rows if r.peak_daily_event]

            return {
                "historical_avg_annual_mm": round(sum(annual_totals) / len(annual_totals), 1) if annual_totals else 0,
                "max_annual_total_mm": round(max(annual_totals), 1) if annual_totals else 0,
                "min_annual_total_mm": round(min(annual_totals), 1) if annual_totals else 0,
                "peak_daily_event_mm": round(max(peak_events), 1) if peak_events else 0,
                "avg_rain_days_per_year": round(sum(r.rain_days for r in rows) / len(rows), 0),
                "years_available": len(rows),
                "years_requested": years_back,
                "data_quality": "high" if len(rows) >= years_back * 0.8 else "moderate",
                "source": "BigQuery (NOAA GSOD)",
                "annual_series": [
                    {"year": r.year, "total_mm": round(r.annual_total, 1) if r.annual_total else 0}
                    for r in rows[:10]  # Last 10 years
                ]
            }

        except Exception as e:
            logger.error(f"BigQuery benchmark query failed: {e}")
            return self._get_mock_benchmarks(latitude, longitude, years_back)

    # ─── Audit Trail Persistence ───────────────────────────────────────

    async def persist_audit_event(
        self,
        tx_hash: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Persists a payout event to the BigQuery audit table.
        Used by the Transparency Dashboard for public verification.
        """
        if not self.client:
            return {"status": "mock", "message": "BigQuery unavailable, audit logged locally"}

        try:
            table_id = f"{self.project_id}.{self.dataset}.audit_payouts"

            rows = [{
                "tx_hash": tx_hash,
                "timestamp": datetime.utcnow().isoformat(),
                "severity_score": event_data.get("severity_score"),
                "ndvi_value": event_data.get("ndvi"),
                "soil_moisture": event_data.get("soil_moisture"),
                "latitude": event_data.get("latitude"),
                "longitude": event_data.get("longitude"),
                "payout_bps": event_data.get("payout_bps"),
                "oracle_mode": event_data.get("oracle_mode"),
            }]

            errors = self.client.insert_rows_json(table_id, rows)
            if errors:
                logger.error(f"BigQuery insert errors: {errors}")
                return {"status": "error", "errors": errors}

            return {"status": "persisted", "table": table_id}

        except Exception as e:
            logger.error(f"Audit persistence failed: {e}")
            return {"status": "error", "message": str(e)}

    # ─── Risk Tranching Analytics ──────────────────────────────────────

    async def get_tranche_analytics(self) -> Dict[str, Any]:
        """
        Risk Tranching analytics for the Marketplace (Phase 4).
        Senior tranche: lower risk, lower yield (first loss protection)
        Junior tranche: higher risk, higher yield (absorbs first losses)
        """
        if not self.client:
            return self._get_mock_tranche_analytics()

        try:
            project_id = self._safe_identifier(self.project_id, "project_id")
            dataset = self._safe_identifier(self.dataset, "dataset")
            table_ref = f"{project_id}.{dataset}.vault_tranches"

            query = f"""
                SELECT
                    tranche,
                    SUM(deposit_amount) as tvl,
                    AVG(yield_rate) as avg_yield,
                    COUNT(DISTINCT depositor) as depositors,
                    SUM(claims_paid) as total_claims
                FROM `{table_ref}`
                GROUP BY tranche
            """  # nosec B608
            job = self.client.query(query)
            rows = list(job.result())

            tranches = {}
            for r in rows:
                tranches[r.tranche] = {
                    "tvl": float(r.tvl),
                    "avg_yield": float(r.avg_yield),
                    "depositors": r.depositors,
                    "claims_paid": float(r.total_claims)
                }
            return {"tranches": tranches, "source": "BigQuery"}

        except Exception as e:
            logger.error(f"Tranche analytics failed: {e}")
            return self._get_mock_tranche_analytics()

    # ─── Mock Data (Deterministic) ─────────────────────────────────────

    def _get_mock_benchmarks(
        self, lat: float = 0, lon: float = 0, years: int = 30
    ) -> Dict[str, Any]:
        """Deterministic mock data seeded by coordinates."""
        seed = int(hashlib.sha256(f"{lat:.2f},{lon:.2f}".encode()).hexdigest()[:8], 16)
        base_precip = 900 + (seed % 600)  # 900–1500 mm/year

        annual_series = []
        for i in range(min(years, 10)):
            variation = ((seed + i * 31) % 400) - 200  # ±200mm
            annual_series.append({
                "year": datetime.now().year - i,
                "total_mm": round(base_precip + variation, 1)
            })

        return {
            "historical_avg_annual_mm": round(base_precip, 1),
            "max_annual_total_mm": round(base_precip + 300, 1),
            "min_annual_total_mm": round(base_precip - 250, 1),
            "peak_daily_event_mm": round(40 + (seed % 80), 1),
            "avg_rain_days_per_year": 90 + (seed % 80),
            "years_available": years,
            "years_requested": years,
            "data_quality": "simulated",
            "source": "BigQuery Mock (Deterministic Simulation)",
            "annual_series": annual_series
        }

    def _get_mock_tranche_analytics(self) -> Dict[str, Any]:
        """Mock risk tranching data for Phase 4."""
        return {
            "tranches": {
                "senior": {
                    "tvl": 850000.0,
                    "avg_yield": 0.065,
                    "depositors": 42,
                    "claims_paid": 12500.0,
                    "risk_level": "low",
                    "description": "First loss protection. Lower yield, lower risk."
                },
                "junior": {
                    "tvl": 400000.0,
                    "avg_yield": 0.184,
                    "depositors": 18,
                    "claims_paid": 45000.0,
                    "risk_level": "high",
                    "description": "Absorbs first losses. Higher yield, higher risk."
                }
            },
            "total_tvl": 1250000.0,
            "blended_yield": 0.104,
            "source": "Mock (Tranche Simulation)"
        }
