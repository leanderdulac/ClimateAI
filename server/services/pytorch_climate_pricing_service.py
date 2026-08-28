"""Climate-adjusted pricing on real Open-Meteo series + LSTM attention (PyTorch).

No synthetic climate. Training uses archive observations. Monte Carlo draws
empirical residuals of that fit — bootstrap of real forecast error, not fake weather.
"""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np

from services.lstm_attention_service import (
    HAS_TORCH,
    LSTMAttentionService,
    select_torch_device,
)

logger = logging.getLogger(__name__)

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_VARS = (
    "temperature_2m_mean",
    "precipitation_sum",
    "surface_pressure_mean",
    "wind_speed_10m_max",
)


def _finite(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return arr
    mask = np.isfinite(arr)
    if mask.all():
        return arr
    if not mask.any():
        return np.array([], dtype=np.float64)
    idx = np.arange(len(arr))
    arr[~mask] = np.interp(idx[~mask], idx[mask], arr[mask])
    return arr


def fetch_openmeteo_daily_archive(
    latitude: float,
    longitude: float,
    days: int = 365,
    timeout: int = 45,
) -> Dict[str, List[float]]:
    """Pull real daily observations from the Open-Meteo archive (UTC)."""
    end = datetime.now(timezone.utc).date() - timedelta(days=5)
    start = end - timedelta(days=max(60, days))
    query = urlencode(
        {
            "latitude": f"{latitude:.4f}",
            "longitude": f"{longitude:.4f}",
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": ",".join(DAILY_VARS),
            "timezone": "UTC",
        }
    )
    req = Request(f"{ARCHIVE_URL}?{query}", headers={"User-Agent": "ClimateWise/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode())
    daily = payload.get("daily") or {}
    dates = daily.get("time") or []
    temp = _finite(np.array(daily.get("temperature_2m_mean") or [], dtype=np.float64))
    precip = _finite(np.array(daily.get("precipitation_sum") or [], dtype=np.float64))
    pressure = _finite(np.array(daily.get("surface_pressure_mean") or [], dtype=np.float64))
    wind = _finite(np.array(daily.get("wind_speed_10m_max") or [], dtype=np.float64))
    n = min(len(dates), len(temp), len(precip), len(pressure), len(wind))
    if n < 40:
        raise ValueError(f"Open-Meteo archive returned only {n} complete days")
    return {
        "dates": dates[:n],
        "temperature": temp[:n].tolist(),
        "precipitation": precip[:n].tolist(),
        "pressure": pressure[:n].tolist(),
        "wind": wind[:n].tolist(),
        "start": dates[0],
        "end": dates[n - 1],
        "n_obs": n,
        "latitude": latitude,
        "longitude": longitude,
        "source": "Open-Meteo archive",
    }


def climate_exceedance_multipliers(
    historical: np.ndarray,
    simulated: np.ndarray,
    quantile: float = 0.95,
) -> Dict[str, float]:
    """Compare simulated vs historical tail of real precipitation."""
    hist = np.asarray(historical, dtype=np.float64)
    sim = np.asarray(simulated, dtype=np.float64)
    if hist.size < 20 or sim.size < 20:
        raise ValueError("not enough observations for tail comparison")
    threshold = float(np.quantile(hist, quantile))
    lambda_hist = float(np.mean(hist > threshold))
    lambda_sim = float(np.mean(sim > threshold))
    freq_mult = lambda_sim / max(lambda_hist, 1e-6)
    tail_hist = hist[hist > threshold]
    tail_sim = sim[sim > threshold]
    sev_hist = float(np.mean(tail_hist)) if tail_hist.size else threshold
    sev_sim = float(np.mean(tail_sim)) if tail_sim.size else threshold
    sev_mult = sev_sim / max(sev_hist, 1e-6)
    return {
        "threshold_mm": threshold,
        "historical_exceedance": lambda_hist,
        "simulated_exceedance": lambda_sim,
        "frequency_multiplier": float(np.clip(freq_mult, 0.7, 1.8)),
        "severity_multiplier": float(np.clip(sev_mult, 0.7, 1.8)),
        "historical_tail_mean_mm": sev_hist,
        "simulated_tail_mean_mm": sev_sim,
    }


class PyTorchClimatePricingService:
    def __init__(self) -> None:
        self.device = select_torch_device() if HAS_TORCH else None

    async def simulate(
        self,
        latitude: float,
        longitude: float,
        *,
        asset_value: float,
        severity_amount: float,
        frequency_pct: float,
        coverage_period_years: int = 1,
        days: int = 365,
        epochs: int = 12,
        sequence_length: int = 14,
        n_sims: int = 256,
        horizon_days: int = 30,
    ) -> Dict[str, Any]:
        if not HAS_TORCH:
            raise RuntimeError("PyTorch is not installed")

        archive = await _async_archive(latitude, longitude, days)
        oni, regime = await _async_oni()
        n = archive["n_obs"]
        enso = [oni] * n if oni is not None else [0.0] * n
        features_used = ["temperature", "precipitation", "pressure", "wind"]
        if oni is not None:
            features_used.append("enso_oni")

        temp = archive["temperature"]
        precip = archive["precipitation"]
        pressure = archive["pressure"]
        wind = archive["wind"]

        service = LSTMAttentionService(device=self.device)
        train_metrics = service.train_model(
            temperature=temp,
            precipitation=precip,
            pressure=pressure,
            nao_index=wind,
            enso_phase=enso,
            targets=precip,
            sequence_length=sequence_length,
            epochs=epochs,
            batch_size=32,
            validation_split=0.15,
        )

        pred = service.predict(
            temperature=temp,
            precipitation=precip,
            pressure=pressure,
            nao_index=wind,
            enso_phase=enso,
            sequence_length=sequence_length,
        )
        y_hat = float(pred["predictions"][0])

        residuals = _in_sample_residuals(
            service, temp, precip, pressure, wind, enso, sequence_length
        )
        simulated = _bootstrap_paths(
            y_hat=y_hat,
            residuals=residuals,
            n_sims=n_sims,
            horizon_days=horizon_days,
            device=_bootstrap_device(),
        )
        multipliers = climate_exceedance_multipliers(np.asarray(precip), simulated)

        adj_freq = float(frequency_pct) * multipliers["frequency_multiplier"]
        adj_sev = float(severity_amount) * multipliers["severity_multiplier"]
        expected_loss = (adj_freq / 100.0) * min(adj_sev, asset_value) * coverage_period_years
        loading = 0.35 + 0.15
        climate_premium = expected_loss * (1.0 + loading)

        return {
            "device": str(service.device),
            "torch": True,
            "observations": {
                "n": n,
                "start": archive["start"],
                "end": archive["end"],
                "source": archive["source"],
                "features": features_used,
                "enso_oni": oni,
                "enso_regime": regime,
            },
            "lstm": {
                "epochs": epochs,
                "sequence_length": sequence_length,
                "final_train_loss": train_metrics.get("final_train_loss"),
                "final_val_loss": train_metrics.get("final_val_loss"),
                "next_day_precip_mm": y_hat,
            },
            "simulation": {
                "n_sims": n_sims,
                "horizon_days": horizon_days,
                "method": "empirical residual bootstrap on LSTM fit to Open-Meteo archive",
                **multipliers,
            },
            "pricing": {
                "input_frequency_pct": frequency_pct,
                "input_severity_amount": severity_amount,
                "adjusted_frequency_pct": adj_freq,
                "adjusted_severity_amount": adj_sev,
                "expected_loss": expected_loss,
                "climate_loaded_premium": climate_premium,
            },
        }


async def _async_archive(lat: float, lon: float, days: int) -> Dict[str, Any]:
    import asyncio

    return await asyncio.to_thread(fetch_openmeteo_daily_archive, lat, lon, days)


async def _async_oni() -> Tuple[Optional[float], Optional[str]]:
    try:
        from services.enso_service import ENSOService

        snap = await ENSOService().get_latest_snapshot()
        value = snap.get("oni", snap.get("roni"))
        regime = snap.get("regime_label")
        return (float(value) if value is not None else None), (
            str(regime) if regime else None
        )
    except Exception as exc:
        logger.warning("ENSO unavailable: %s", exc)
        return None, None


def _in_sample_residuals(
    service: LSTMAttentionService,
    temp: List[float],
    precip: List[float],
    pressure: List[float],
    wind: List[float],
    enso: List[float],
    seq_len: int,
) -> np.ndarray:
    import torch

    if service.model is None:
        return np.array([0.0])
    features = service.prepare_climate_features(temp, precip, pressure, wind, enso)
    normalized = service.normalize_features(features)
    X, y = service.create_sequences(normalized, np.array(precip, dtype=np.float64), seq_len)
    if len(X) == 0:
        return np.array([0.0])
    service.model.eval()
    with torch.no_grad():
        pred, _ = service.model(X)
        pred_np = pred.squeeze().detach().cpu().numpy()
        y_np = y.detach().cpu().numpy()
    resid = np.asarray(y_np - pred_np, dtype=np.float64).ravel()
    resid = resid[np.isfinite(resid)]
    return resid if resid.size else np.array([0.0])


def _bootstrap_device():
    return select_torch_device(prefer_mps=True) or select_torch_device()


def _bootstrap_paths(
    *,
    y_hat: float,
    residuals: np.ndarray,
    n_sims: int,
    horizon_days: int,
    device,
) -> np.ndarray:
    import torch

    if residuals.size == 0:
        residuals = np.array([0.0], dtype=np.float64)
    if device is None:
        device = torch.device("cpu")
    res = torch.tensor(residuals, dtype=torch.float32, device=device)
    idx = torch.randint(0, res.numel(), (n_sims, horizon_days), device=device)
    draws = res[idx]
    paths = torch.clamp(y_hat + draws, min=0.0)
    return paths.detach().cpu().numpy().ravel()


pytorch_climate_pricing_service = PyTorchClimatePricingService()
