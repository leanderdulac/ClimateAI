#!/usr/bin/env python3
"""Train LSTM attention on real Open-Meteo archive and price a location (MPS/CPU)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lat", type=float, default=-23.55)
    parser.add_argument("--lon", type=float, default=-46.63)
    parser.add_argument("--asset", type=float, default=250000)
    parser.add_argument("--severity", type=float, default=40000)
    parser.add_argument("--frequency", type=float, default=12)
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--epochs", type=int, default=16)
    parser.add_argument("--sims", type=int, default=512)
    args = parser.parse_args()

    from services.lstm_attention_service import HAS_TORCH, select_torch_device
    from services.pytorch_climate_pricing_service import pytorch_climate_pricing_service

    print("torch", HAS_TORCH, "device", select_torch_device())
    result = await pytorch_climate_pricing_service.simulate(
        args.lat,
        args.lon,
        asset_value=args.asset,
        severity_amount=args.severity,
        frequency_pct=args.frequency,
        days=args.days,
        epochs=args.epochs,
        n_sims=args.sims,
    )
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
