"""
Probabilistic aggregation for Google WeatherNext 2 ensemble members.

Hourly Open-Meteo fields are UTC. Daily statistics are aggregated in
America/Sao_Paulo so parametric day boundaries match Brazilian local time.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

import numpy as np

SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")
UTC_TZ = ZoneInfo("UTC")

DEFAULT_PRECIP_THRESHOLDS_MM = (10.0, 25.0, 50.0, 75.0)
DEFAULT_HEAT_THRESHOLDS_C = (30.0, 35.0, 40.0)
HEAVY_RAIN_MM = 50.0
PERCENTILES = (10, 50, 90)

MEMBER_TEMP_PREFIX = "temperature_2m_member"
MEMBER_PRECIP_PREFIX = "precipitation_member"


@dataclass
class DailyMemberStats:
    date: str
    precip_mm: float
    tmin_c: float
    tmax_c: float
    tmean_c: float


@dataclass
class DailyEnsembleStats:
    date: str
    member_count: int
    temperature_mean_c: float
    temperature_min_c: float
    temperature_max_c: float
    precip_mean_mm: float
    precip_min_mm: float
    precip_max_mm: float
    temperature_p10_c: float
    temperature_p50_c: float
    temperature_p90_c: float
    precip_p10_mm: float
    precip_p50_mm: float
    precip_p90_mm: float
    precip_exceedance: Dict[str, float]
    heat_exceedance: Dict[str, float]
    p_heavy_rain: float
    members: List[DailyMemberStats] = field(default_factory=list)


def extract_member_series(
    hourly: Mapping[str, Sequence[Any]],
    prefix: str,
    include_control: Optional[str] = None,
) -> Dict[str, List[float]]:
    """Return member_id -> hourly series, optionally including the control run."""
    members: Dict[str, List[float]] = {}
    if include_control and include_control in hourly:
        members["00"] = _as_float_list(hourly[include_control])
    for key, values in hourly.items():
        if not key.startswith(prefix):
            continue
        member_id = key[len(prefix) :]
        if not member_id.isdigit():
            continue
        members[member_id.zfill(2)] = _as_float_list(values)
    return dict(sorted(members.items()))


def _as_float_list(values: Sequence[Any]) -> List[float]:
    out: List[float] = []
    for value in values:
        if value is None:
            out.append(float("nan"))
        else:
            out.append(float(value))
    return out


def parse_utc_times(times: Sequence[str]) -> List[datetime]:
    parsed: List[datetime] = []
    for raw in times:
        text = str(raw).replace("Z", "")
        if "T" in text:
            dt = datetime.fromisoformat(text)
        else:
            dt = datetime.fromisoformat(f"{text}T00:00:00")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC_TZ)
        parsed.append(dt.astimezone(UTC_TZ))
    return parsed


def percentile(values: Sequence[float], q: float) -> float:
    clean = [float(v) for v in values if v is not None and not np.isnan(v)]
    if not clean:
        return float("nan")
    return float(np.percentile(clean, q))


def exceedance_probability(values: Sequence[float], threshold: float, *, ge: bool = True) -> float:
    clean = [float(v) for v in values if v is not None and not np.isnan(v)]
    if not clean:
        return 0.0
    if ge:
        hits = sum(1 for v in clean if v >= threshold)
    else:
        hits = sum(1 for v in clean if v <= threshold)
    return hits / len(clean)


def hourly_percentiles(
    members: Mapping[str, Sequence[float]],
) -> Dict[str, List[float]]:
    if not members:
        return {"p10": [], "p50": [], "p90": []}
    length = min(len(series) for series in members.values())
    p10: List[float] = []
    p50: List[float] = []
    p90: List[float] = []
    for idx in range(length):
        column = [series[idx] for series in members.values()]
        p10.append(percentile(column, 10))
        p50.append(percentile(column, 50))
        p90.append(percentile(column, 90))
    return {"p10": p10, "p50": p50, "p90": p90}


def aggregate_daily_members(
    times_utc: Sequence[datetime],
    temp_members: Mapping[str, Sequence[float]],
    precip_members: Mapping[str, Sequence[float]],
    tz: ZoneInfo = SAO_PAULO_TZ,
) -> Dict[str, Dict[str, DailyMemberStats]]:
    """date -> member_id -> DailyMemberStats in the given timezone."""
    buckets: Dict[str, Dict[str, Dict[str, List[float]]]] = defaultdict(
        lambda: defaultdict(lambda: {"temp": [], "precip": []})
    )
    member_ids = sorted(set(temp_members) | set(precip_members))
    for hour_idx, utc_dt in enumerate(times_utc):
        local_date = utc_dt.astimezone(tz).date().isoformat()
        for member_id in member_ids:
            temp_series = temp_members.get(member_id)
            precip_series = precip_members.get(member_id)
            if temp_series is not None and hour_idx < len(temp_series):
                buckets[local_date][member_id]["temp"].append(temp_series[hour_idx])
            if precip_series is not None and hour_idx < len(precip_series):
                buckets[local_date][member_id]["precip"].append(precip_series[hour_idx])

    daily: Dict[str, Dict[str, DailyMemberStats]] = {}
    for date, members in buckets.items():
        daily[date] = {}
        for member_id, series in members.items():
            temps = [v for v in series["temp"] if not np.isnan(v)]
            precips = [v for v in series["precip"] if not np.isnan(v)]
            if not temps and not precips:
                continue
            daily[date][member_id] = DailyMemberStats(
                date=date,
                precip_mm=float(np.nansum(precips)) if precips else 0.0,
                tmin_c=float(np.nanmin(temps)) if temps else float("nan"),
                tmax_c=float(np.nanmax(temps)) if temps else float("nan"),
                tmean_c=float(np.nanmean(temps)) if temps else float("nan"),
            )
    return daily


def summarize_daily_ensemble(
    daily_members: Mapping[str, Mapping[str, DailyMemberStats]],
    precip_thresholds: Sequence[float] = DEFAULT_PRECIP_THRESHOLDS_MM,
    heat_thresholds: Sequence[float] = DEFAULT_HEAT_THRESHOLDS_C,
    include_members: bool = False,
) -> List[DailyEnsembleStats]:
    summaries: List[DailyEnsembleStats] = []
    for date in sorted(daily_members):
        members = list(daily_members[date].values())
        if not members:
            continue
        tmeans = [m.tmean_c for m in members]
        tmins = [m.tmin_c for m in members]
        tmaxs = [m.tmax_c for m in members]
        precips = [m.precip_mm for m in members]
        precip_exceedance = {
            f"ge_{int(threshold)}mm": round(exceedance_probability(precips, threshold), 4)
            for threshold in precip_thresholds
        }
        heat_exceedance = {
            f"ge_{int(threshold)}c": round(exceedance_probability(tmaxs, threshold), 4)
            for threshold in heat_thresholds
        }
        summaries.append(
            DailyEnsembleStats(
                date=date,
                member_count=len(members),
                temperature_mean_c=_safe_mean(tmeans),
                temperature_min_c=_safe_min(tmins),
                temperature_max_c=_safe_max(tmaxs),
                precip_mean_mm=_safe_mean(precips),
                precip_min_mm=_safe_min(precips),
                precip_max_mm=_safe_max(precips),
                temperature_p10_c=round(percentile(tmeans, 10), 3),
                temperature_p50_c=round(percentile(tmeans, 50), 3),
                temperature_p90_c=round(percentile(tmeans, 90), 3),
                precip_p10_mm=round(percentile(precips, 10), 3),
                precip_p50_mm=round(percentile(precips, 50), 3),
                precip_p90_mm=round(percentile(precips, 90), 3),
                precip_exceedance=precip_exceedance,
                heat_exceedance=heat_exceedance,
                p_heavy_rain=round(exceedance_probability(precips, HEAVY_RAIN_MM), 4),
                members=members if include_members else [],
            )
        )
    return summaries


def daily_to_dict(stats: DailyEnsembleStats) -> Dict[str, Any]:
    payload = asdict(stats)
    if not stats.members:
        payload.pop("members", None)
    return payload


def build_hourly_fan(
    times_utc: Sequence[datetime],
    temp_members: Mapping[str, Sequence[float]],
    precip_members: Mapping[str, Sequence[float]],
    tz: ZoneInfo = SAO_PAULO_TZ,
) -> List[Dict[str, Any]]:
    temp_pct = hourly_percentiles(temp_members)
    precip_pct = hourly_percentiles(precip_members)
    length = min(len(times_utc), len(temp_pct["p50"]), len(precip_pct["p50"]))
    fan: List[Dict[str, Any]] = []
    for idx in range(length):
        local = times_utc[idx].astimezone(tz)
        fan.append(
            {
                "time_utc": times_utc[idx].isoformat(),
                "time_local": local.isoformat(),
                "temperature_p10_c": _round_or_none(temp_pct["p10"][idx]),
                "temperature_p50_c": _round_or_none(temp_pct["p50"][idx]),
                "temperature_p90_c": _round_or_none(temp_pct["p90"][idx]),
                "precip_p10_mm": _round_or_none(precip_pct["p10"][idx]),
                "precip_p50_mm": _round_or_none(precip_pct["p50"][idx]),
                "precip_p90_mm": _round_or_none(precip_pct["p90"][idx]),
            }
        )
    return fan


def weathernext_oracle_vote(
    daily: Sequence[DailyEnsembleStats],
    *,
    trigger_type: str,
    threshold: float,
    condition: str = "above",
    probability_cutoff: float = 0.5,
) -> Dict[str, Any]:
    """
    WeatherNext votes YES when the majority of members (P >= cutoff)
    exceed the parametric trigger on any forecast day.

    This is a probabilistic vote. It does not replace observed-source votes.
    """
    if not daily:
        return {
            "source": "google_weathernext2_ensemble",
            "vote": False,
            "reason": "no_ensemble_days",
            "probability": 0.0,
        }

    ge = condition != "below" and trigger_type != "drought"
    best_p = 0.0
    best_date = daily[0].date
    precip_types = {"precipitation", "rainfall", "flood", "drought"}
    for day in daily:
        if day.members:
            if trigger_type in precip_types:
                values = [m.precip_mm for m in day.members]
            else:
                values = [m.tmax_c for m in day.members]
            p = exceedance_probability(values, threshold, ge=ge)
        elif trigger_type in precip_types:
            key = f"ge_{int(threshold)}mm"
            p = day.precip_exceedance.get(key)
            if p is None:
                p = 1.0 if (day.precip_p50_mm >= threshold) == ge or (
                    not ge and day.precip_p50_mm <= threshold
                ) else 0.0
        else:
            key = f"ge_{int(threshold)}c"
            p = day.heat_exceedance.get(key)
            if p is None:
                p = 1.0 if (day.temperature_p50_c >= threshold) == ge or (
                    not ge and day.temperature_p50_c <= threshold
                ) else 0.0
        if p >= best_p:
            best_p = p
            best_date = day.date

    vote = best_p >= probability_cutoff
    return {
        "source": "google_weathernext2_ensemble",
        "vote": vote,
        "probability": round(best_p, 4),
        "probability_cutoff": probability_cutoff,
        "threshold": threshold,
        "condition": "below" if not ge else "above",
        "trigger_type": trigger_type,
        "best_date": best_date,
        "reason": "majority_members_exceed_trigger" if vote else "below_probability_cutoff",
    }


def pricing_exceedance_inputs(
    daily: Sequence[DailyEnsembleStats],
    precip_thresholds: Iterable[float] = DEFAULT_PRECIP_THRESHOLDS_MM,
    heat_thresholds: Iterable[float] = DEFAULT_HEAT_THRESHOLDS_C,
) -> Dict[str, Any]:
    """Horizon-max exceedance probabilities for FIMCE / parametric pricing."""
    precip: Dict[str, float] = {}
    heat: Dict[str, float] = {}
    p_heavy = 0.0
    for day in daily:
        for threshold in precip_thresholds:
            key = f"ge_{int(threshold)}mm"
            precip[key] = max(precip.get(key, 0.0), day.precip_exceedance.get(key, 0.0))
        for threshold in heat_thresholds:
            key = f"ge_{int(threshold)}c"
            heat[key] = max(heat.get(key, 0.0), day.heat_exceedance.get(key, 0.0))
        p_heavy = max(p_heavy, day.p_heavy_rain)
    return {
        "precip_exceedance": precip,
        "heat_exceedance": heat,
        "p_heavy_rain": round(p_heavy, 4),
        "horizon_days": len(daily),
        "source": "google_weathernext2_ensemble",
    }


def apply_exceedance_loading(
    base_premium: float,
    exceedance_probability: float,
    loading_factor: float = 0.25,
) -> float:
    """Parametric loading: premium * (1 + k * P(trigger))."""
    p = min(max(float(exceedance_probability), 0.0), 1.0)
    return float(base_premium) * (1.0 + float(loading_factor) * p)


def _safe_mean(values: Sequence[float]) -> float:
    clean = [v for v in values if not np.isnan(v)]
    return round(float(np.mean(clean)), 3) if clean else float("nan")


def _safe_min(values: Sequence[float]) -> float:
    clean = [v for v in values if not np.isnan(v)]
    return round(float(np.min(clean)), 3) if clean else float("nan")


def _safe_max(values: Sequence[float]) -> float:
    clean = [v for v in values if not np.isnan(v)]
    return round(float(np.max(clean)), 3) if clean else float("nan")


def _round_or_none(value: float, digits: int = 3) -> Optional[float]:
    if value is None or np.isnan(value):
        return None
    return round(float(value), digits)


def process_open_meteo_hourly(
    payload: Mapping[str, Any],
    *,
    include_members: bool = False,
    precip_thresholds: Sequence[float] = DEFAULT_PRECIP_THRESHOLDS_MM,
    heat_thresholds: Sequence[float] = DEFAULT_HEAT_THRESHOLDS_C,
) -> Tuple[List[Dict[str, Any]], List[DailyEnsembleStats], Dict[str, Any]]:
    hourly = payload.get("hourly") or {}
    times = parse_utc_times(hourly.get("time") or [])
    temp_members = extract_member_series(hourly, MEMBER_TEMP_PREFIX, include_control="temperature_2m")
    precip_members = extract_member_series(hourly, MEMBER_PRECIP_PREFIX, include_control="precipitation")
    daily_members = aggregate_daily_members(times, temp_members, precip_members)
    daily = summarize_daily_ensemble(
        daily_members,
        precip_thresholds=precip_thresholds,
        heat_thresholds=heat_thresholds,
        include_members=include_members,
    )
    fan = build_hourly_fan(times, temp_members, precip_members)
    meta = {
        "member_count": max(len(temp_members), len(precip_members)),
        "hourly_steps": len(times),
        "timezone_daily": "America/Sao_Paulo",
        "timezone_hourly_source": "UTC",
        "model": payload.get("model") or "google_weathernext2_ensemble",
    }
    return fan, daily, meta
