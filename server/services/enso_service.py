"""
ENSO service for ClimateWise.

Provides:
- RONI/ONI ingestion from NOAA CPC public pages
- ENSO regime classification with persistence check (5 overlapping seasons)
- ClimateWise-oriented ENSO scoring and probabilities
"""

import logging
import math
import re
from html import unescape
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lib.resilient_http_client import create_resilient_client
from models.sqlalchemy_models import ClimateEnsoSignal

logger = logging.getLogger(__name__)


class ENSOService:
    """Service for ENSO signal ingestion and scoring."""

    RONI_URL = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/"
    ONI_URL = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php"

    _SEASON_ORDER = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]
    _SEASON_END_MONTH = {
        "DJF": 2,
        "JFM": 3,
        "FMA": 4,
        "MAM": 5,
        "AMJ": 6,
        "MJJ": 7,
        "JJA": 8,
        "JAS": 9,
        "ASO": 10,
        "SON": 11,
        "OND": 12,
        "NDJ": 1,
    }

    def __init__(self) -> None:
        self.client = create_resilient_client("noaa_enso", "https://www.cpc.ncep.noaa.gov")

    async def _fetch_html(self, absolute_url: str) -> str:
        """Fetch page HTML via resilient client."""
        path = absolute_url.replace("https://www.cpc.ncep.noaa.gov", "")
        response = await self.client.get(path)
        response.raise_for_status()
        return response.text

    @classmethod
    def _parse_index_table(cls, html: str) -> List[Dict[str, Any]]:
        """Parse seasonal index tables (Year x seasons) from CPC pages."""
        table_pattern = re.compile(r"<table[^>]*>(.*?)</table>", re.IGNORECASE | re.DOTALL)
        row_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
        cell_pattern = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.IGNORECASE | re.DOTALL)
        tag_pattern = re.compile(r"<[^>]+>")

        def normalize_header(header_text: str) -> str:
            token = header_text.replace("\xa0", " ").strip().split(" ")[0].upper()
            if token == "YEAR":
                return "Year"
            for season in cls._SEASON_ORDER:
                if token == season:
                    return season
            return header_text.strip()

        for table_html in table_pattern.findall(html):
            rows = row_pattern.findall(table_html)
            if not rows:
                continue

            header_cells_raw = cell_pattern.findall(rows[0])
            headers = [
                normalize_header(unescape(tag_pattern.sub("", c)).strip())
                for c in header_cells_raw
            ]
            if "Year" not in headers:
                continue

            year_idx = headers.index("Year")
            season_indices = {
                season: headers.index(season)
                for season in cls._SEASON_ORDER
                if season in headers
            }
            if len(season_indices) < 6:
                continue

            parsed: List[Dict[str, Any]] = []
            for row_html in rows[1:]:
                cells_raw = cell_pattern.findall(row_html)
                cells = [unescape(tag_pattern.sub("", c)).strip() for c in cells_raw]
                if len(cells) <= year_idx:
                    continue

                try:
                    year = int(float(cells[year_idx]))
                except Exception:
                    continue

                for season, idx in season_indices.items():
                    if len(cells) <= idx:
                        continue
                    value_text = cells[idx].replace("\xa0", " ").strip()
                    if not value_text or value_text in {"-", "--"}:
                        continue
                    try:
                        value = float(value_text)
                    except Exception:
                        continue
                    parsed.append({"year": year, "season": season, "value": value})

            if parsed:
                parsed.sort(key=lambda x: (x["year"], cls._SEASON_ORDER.index(x["season"])))
                return parsed

        # Fallback for pages exposing markdown-like pipe tables in text content.
        text = unescape(tag_pattern.sub(" ", html))
        lines = [ln.strip() for ln in text.splitlines() if "|" in ln]
        header_line = None
        for ln in lines:
            if "| Year |" in ln and "| DJF |" in ln:
                header_line = ln
                break

        if header_line:
            headers = [x.strip() for x in header_line.strip().strip("|").split("|")]
            if "Year" in headers:
                year_idx = headers.index("Year")
                season_indices = {
                    season: headers.index(season)
                    for season in cls._SEASON_ORDER
                    if season in headers
                }
                parsed: List[Dict[str, Any]] = []
                for ln in lines:
                    cells = [x.strip() for x in ln.strip().strip("|").split("|")]
                    if len(cells) <= year_idx:
                        continue
                    try:
                        year = int(float(cells[year_idx]))
                    except Exception:
                        continue
                    for season, idx in season_indices.items():
                        if len(cells) <= idx:
                            continue
                        value_text = cells[idx]
                        if not value_text or value_text in {"-", "--"}:
                            continue
                        try:
                            value = float(value_text)
                        except Exception:
                            continue
                        parsed.append({"year": year, "season": season, "value": value})

                if parsed:
                    parsed.sort(key=lambda x: (x["year"], cls._SEASON_ORDER.index(x["season"])))
                    return parsed

        # Direct fallback: parse rows like <tr><th><p>2026</p></th><td>...</td>...</tr>
        row_pattern_direct = re.compile(
            r"<tr[^>]*>\s*<th[^>]*>.*?<p>(\d{4})</p>.*?</th>(.*?)</tr>",
            re.IGNORECASE | re.DOTALL,
        )
        value_pattern = re.compile(r">\s*([-+]?\d+(?:\.\d+)?)\s*<")

        parsed_direct: List[Dict[str, Any]] = []
        for year_text, remainder in row_pattern_direct.findall(html):
            try:
                year = int(year_text)
            except Exception:
                continue

            values = [float(v) for v in value_pattern.findall(remainder)]
            if not values:
                continue

            for idx, value in enumerate(values[: len(cls._SEASON_ORDER)]):
                season = cls._SEASON_ORDER[idx]
                parsed_direct.append({"year": year, "season": season, "value": value})

        if parsed_direct:
            parsed_direct.sort(key=lambda x: (x["year"], cls._SEASON_ORDER.index(x["season"])))
            return parsed_direct

        raise ValueError("No seasonal ENSO table found in source HTML")

    @staticmethod
    def _count_consecutive(series: List[Dict[str, Any]], threshold: float) -> int:
        """Count consecutive values at the end satisfying >= threshold or <= threshold."""
        count = 0
        if threshold >= 0:
            for item in reversed(series):
                if item["value"] >= threshold:
                    count += 1
                else:
                    break
        else:
            for item in reversed(series):
                if item["value"] <= threshold:
                    count += 1
                else:
                    break
        return count

    @staticmethod
    def _logistic(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-x))

    @classmethod
    def _reference_date_from_season(cls, year: int, season: str) -> date:
        """Map season label to a reference month-end date."""
        month = cls._SEASON_END_MONTH.get(season, 12)
        ref_year = year - 1 if season == "DJF" else year
        return date(ref_year, month, 1)

    async def get_roni_series(self) -> List[Dict[str, Any]]:
        html = await self._fetch_html(self.RONI_URL)
        return self._parse_index_table(html)

    async def get_oni_series(self) -> List[Dict[str, Any]]:
        html = await self._fetch_html(self.ONI_URL)
        return self._parse_index_table(html)

    async def get_latest_snapshot(self) -> Dict[str, Any]:
        """Build latest ENSO snapshot with ClimateWise-oriented scoring."""
        roni_series = await self.get_roni_series()
        if not roni_series:
            raise ValueError("RONI series is empty")

        latest_roni = roni_series[-1]
        prev_roni = roni_series[-2] if len(roni_series) >= 2 else latest_roni

        oni_series: List[Dict[str, Any]] = []
        latest_oni: Optional[Dict[str, Any]] = None
        try:
            oni_series = await self.get_oni_series()
            if oni_series:
                latest_oni = oni_series[-1]
        except Exception as exc:
            logger.warning("Unable to fetch ONI series: %s", exc)

        warm_windows = self._count_consecutive(roni_series, 0.5)
        cold_windows = self._count_consecutive(roni_series, -0.5)

        roni = float(latest_roni["value"])
        oni = float(latest_oni["value"]) if latest_oni else roni
        roni_slope = float(latest_roni["value"] - prev_roni["value"])

        if warm_windows >= 5:
            regime_label = "el_nino"
            confidence = "high"
        elif cold_windows >= 5:
            regime_label = "la_nina"
            confidence = "high"
        elif roni >= 0.5:
            regime_label = "warming_transition"
            confidence = "medium"
        elif roni <= -0.5:
            regime_label = "cooling_transition"
            confidence = "medium"
        else:
            regime_label = "neutral"
            confidence = "low"

        # Score aligned with KB formula, with unavailable SOI/OLR neutralized to 0.
        enso_score = (1.0 * roni) + (0.3 * oni) + (0.2 * roni_slope)
        p_el_nino = self._logistic(enso_score - 0.5)
        p_la_nina = self._logistic(-enso_score - 0.5)
        p_neutral = max(0.0, 1.0 - max(p_el_nino, p_la_nina))

        reference_date = self._reference_date_from_season(
            int(latest_roni["year"]), str(latest_roni["season"])
        )

        provisional_flag = (
            latest_roni["year"] >= datetime.utcnow().year
            or len(roni_series) < 24
        )

        return {
            "reference_date": reference_date,
            "roni": roni,
            "oni": oni,
            "soi": None,
            "olr": None,
            "nino12": None,
            "nino3": None,
            "nino34": roni,
            "nino4": None,
            "regime_label": regime_label,
            "regime_confidence": confidence,
            "provisional_flag": provisional_flag,
            "source_url": self.RONI_URL,
            "ingestion_timestamp": datetime.utcnow(),
            "enso_score": enso_score,
            "p_el_nino": p_el_nino,
            "p_la_nina": p_la_nina,
            "p_neutral": p_neutral,
            "coupling_score": None,
            "transition_score": roni_slope,
            "impact_risk_modifier": 1.0 + 0.15 * abs(roni),
            "metadata": {
                "warm_windows": warm_windows,
                "cold_windows": cold_windows,
                "latest_season": latest_roni["season"],
                "latest_year": latest_roni["year"],
                "roni_source": self.RONI_URL,
                "oni_source": self.ONI_URL,
            },
        }

    async def persist_snapshot(
        self,
        db: AsyncSession,
        snapshot: Dict[str, Any],
    ) -> ClimateEnsoSignal:
        """Persist latest ENSO snapshot, updating same reference date row when present."""
        stmt = select(ClimateEnsoSignal).where(
            ClimateEnsoSignal.reference_date == snapshot["reference_date"]
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            target = existing
        else:
            target = ClimateEnsoSignal(reference_date=snapshot["reference_date"])
            db.add(target)

        target.roni = snapshot.get("roni")
        target.oni = snapshot.get("oni")
        target.soi = snapshot.get("soi")
        target.olr = snapshot.get("olr")
        target.nino12 = snapshot.get("nino12")
        target.nino3 = snapshot.get("nino3")
        target.nino34 = snapshot.get("nino34")
        target.nino4 = snapshot.get("nino4")
        target.regime_label = snapshot.get("regime_label")
        target.regime_confidence = snapshot.get("regime_confidence")
        target.provisional_flag = snapshot.get("provisional_flag", False)
        target.source_url = snapshot.get("source_url")
        target.ingestion_timestamp = snapshot.get("ingestion_timestamp", datetime.utcnow())
        target.enso_score = snapshot.get("enso_score")
        target.p_el_nino = snapshot.get("p_el_nino")
        target.p_la_nina = snapshot.get("p_la_nina")
        target.p_neutral = snapshot.get("p_neutral")
        target.coupling_score = snapshot.get("coupling_score")
        target.transition_score = snapshot.get("transition_score")
        target.impact_risk_modifier = snapshot.get("impact_risk_modifier")
        target.metadata_json = snapshot.get("metadata")

        await db.commit()
        await db.refresh(target)
        return target
