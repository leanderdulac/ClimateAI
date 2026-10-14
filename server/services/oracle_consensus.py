"""
Multi-source oracle consensus.

Existing rule (unchanged): payout requires 2 of the 3 observed sources
(INMET, NOAA, Open-Meteo) to agree that the parametric trigger is met.

WeatherNext 2 is an *additional* voter. It does not change the required
count of 2 and it does not replace an observed source:

- Consensus still triggers when at least 2 sources vote YES.
- If WeatherNext is disabled or unavailable, the original 2-of-3 path
  is used exactly as before.
- When enabled, WeatherNext votes YES iff P(members exceed the trigger)
  >= 0.5 on any forecast day (majority of the 63-member ensemble).
- WeatherNext can be one of the two agreeing sources, or a third/fourth
  confirming vote that raises confidence without changing the threshold.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from config.config import settings
from services.weathernext_ensemble_service import (
    OutsideBrazilError,
    WeatherNextDisabledError,
    get_weathernext_service,
)

logger = logging.getLogger(__name__)

CORE_SOURCES = ("inmet", "noaa", "openmeteo")
WEATHERNEXT_SOURCE = "google_weathernext2_ensemble"
REQUIRED_YES_VOTES = 2


def weathernext_enabled() -> bool:
    return bool(getattr(settings, "WEATHERNEXT_ENABLED", True))


async def evaluate_oracle_consensus(
    *,
    latitude: float,
    longitude: float,
    index_type: str,
    trigger_value: float,
    trigger_condition: str = "above",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    oracle_service: Any = None,
    weathernext_service: Any = None,
    include_weathernext: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Collect votes from INMET / NOAA / Open-Meteo and optionally WeatherNext.

    `required_votes` stays 2 so existing consensus logic is preserved.
    """
    if oracle_service is None:
        from blockchain.hathor.oracle_service import get_climate_oracle_service

        oracle_service = get_climate_oracle_service()

    end = end_date or datetime.utcnow()
    start = start_date or (end - timedelta(days=7))
    use_weathernext = (
        weathernext_enabled() if include_weathernext is None else include_weathernext
    )

    votes: List[Dict[str, Any]] = []
    for source in CORE_SOURCES:
        votes.append(
            _observed_source_vote(
                oracle_service,
                source=source,
                index_type=index_type,
                latitude=latitude,
                longitude=longitude,
                start_date=start,
                end_date=end,
                trigger_value=trigger_value,
                trigger_condition=trigger_condition,
            )
        )

    weathernext_vote: Optional[Dict[str, Any]] = None
    if use_weathernext:
        weathernext_vote = await _weathernext_vote(
            latitude=latitude,
            longitude=longitude,
            index_type=index_type,
            trigger_value=trigger_value,
            trigger_condition=trigger_condition,
            service=weathernext_service,
        )
        if weathernext_vote is not None:
            votes.append(weathernext_vote)

    yes_votes = [v for v in votes if v.get("vote") and v.get("available")]
    available = [v for v in votes if v.get("available")]
    consensus = len(yes_votes) >= REQUIRED_YES_VOTES
    agreeing_sources = [v["source"] for v in yes_votes]

    return {
        "consensus": consensus,
        "required_votes": REQUIRED_YES_VOTES,
        "yes_votes": len(yes_votes),
        "available_sources": len(available),
        "agreeing_sources": agreeing_sources,
        "votes": votes,
        "weathernext_enabled": use_weathernext,
        "weathernext_voted": weathernext_vote is not None,
        "rule": (
            "2-of-3 observed sources (INMET, NOAA, Open-Meteo). "
            "WeatherNext is an optional fourth voter: YES when "
            "P(ensemble members exceed trigger) >= 0.5. "
            "Required YES count stays 2."
        ),
        "index_type": index_type,
        "trigger_value": trigger_value,
        "trigger_condition": trigger_condition,
        "location": {"lat": latitude, "lon": longitude},
    }


def _observed_source_vote(
    oracle_service: Any,
    *,
    source: str,
    index_type: str,
    latitude: float,
    longitude: float,
    start_date: datetime,
    end_date: datetime,
    trigger_value: float,
    trigger_condition: str,
) -> Dict[str, Any]:
    try:
        index = oracle_service.get_climate_index(
            index_type=index_type,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            trigger_value=trigger_value,
            trigger_condition=trigger_condition,
            source=source,
        )
        return {
            "source": source,
            "vote": bool(index.trigger_met),
            "available": True,
            "value": index.value,
            "kind": "observed",
        }
    except Exception as exc:
        logger.warning("Oracle source %s failed: %s", source, exc)
        return {
            "source": source,
            "vote": False,
            "available": False,
            "value": None,
            "kind": "observed",
            "error": str(exc),
        }


async def _weathernext_vote(
    *,
    latitude: float,
    longitude: float,
    index_type: str,
    trigger_value: float,
    trigger_condition: str,
    service: Any = None,
) -> Optional[Dict[str, Any]]:
    try:
        svc = service or get_weathernext_service()
        result = await svc.forecast_point(latitude, longitude, include_members=True)
        vote = svc.oracle_vote(
            result,
            trigger_type=index_type,
            threshold=trigger_value,
            condition=trigger_condition,
        )
        vote["available"] = True
        vote["kind"] = "ensemble_forecast"
        vote["value"] = vote.get("probability")
        return vote
    except (WeatherNextDisabledError, OutsideBrazilError) as exc:
        logger.info("WeatherNext vote skipped: %s", exc)
        return {
            "source": WEATHERNEXT_SOURCE,
            "vote": False,
            "available": False,
            "kind": "ensemble_forecast",
            "error": str(exc),
        }
    except Exception as exc:
        logger.warning("WeatherNext vote failed: %s", exc)
        return {
            "source": WEATHERNEXT_SOURCE,
            "vote": False,
            "available": False,
            "kind": "ensemble_forecast",
            "error": str(exc),
        }
