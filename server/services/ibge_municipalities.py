"""IBGE municipality centroids shipped with ClimateWise (~5570 records)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "ibge_municipality_centroids.json"


class MunicipalityNotFound(KeyError):
    """Raised when an IBGE code is not in the shipped catalog."""


@lru_cache(maxsize=1)
def load_catalog() -> Dict[str, object]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Municipality catalog missing: {DATA_PATH}")
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    municipalities = payload.get("municipalities") or []
    by_code = {str(row["ibge_code"]): row for row in municipalities}
    payload["by_code"] = by_code
    return payload


def all_municipalities() -> List[Dict[str, object]]:
    catalog = load_catalog()
    return list(catalog["municipalities"])  # type: ignore[arg-type]


def get_municipality(ibge_code: str) -> Dict[str, object]:
    code = str(ibge_code).strip()
    catalog = load_catalog()
    by_code: Dict[str, Dict[str, object]] = catalog["by_code"]  # type: ignore[assignment]
    row = by_code.get(code)
    if not row:
        raise MunicipalityNotFound(code)
    return row


def find_by_name(name: str, uf: Optional[str] = None) -> List[Dict[str, object]]:
    needle = name.strip().casefold()
    uf_norm = uf.strip().upper() if uf else None
    matches = []
    for row in all_municipalities():
        if str(row["name"]).casefold() != needle:
            continue
        if uf_norm and str(row["uf"]).upper() != uf_norm:
            continue
        matches.append(row)
    return matches


def monte_alegre_records() -> List[Dict[str, object]]:
    return [row for row in all_municipalities() if "Monte Alegre" in str(row["name"])]
