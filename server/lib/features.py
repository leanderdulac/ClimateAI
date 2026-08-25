"""Product feature flags. Default on so existing tests and local dev keep working."""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

from config.config import settings

API_PREFIX = os.getenv("API_PREFIX", "/api/v1").rstrip("/") or "/api/v1"


def current_flags() -> Dict[str, bool]:
    return {
        "atlas": settings.FEATURE_ATLAS,
        "blockchain": settings.FEATURE_BLOCKCHAIN,
        "assistant": settings.FEATURE_ASSISTANT,
    }


def disabled_feature_for_path(path: str) -> Optional[str]:
    """Return the feature name if this path is gated and currently disabled."""
    normalized = path.rstrip("/") or "/"
    prefix = API_PREFIX
    rules: List[Tuple[str, Tuple[str, ...]]] = [
        (
            "atlas",
            (
                f"{prefix}/atlas",
                f"{prefix}/atlas-simulation",
                f"{prefix}/atlas-realtime",
                f"{prefix}/atlas-integration",
                f"{prefix}/atlas-disasters",
            ),
        ),
        (
            "blockchain",
            (
                f"{prefix}/blockchain",
                f"{prefix}/tokenizacao",
            ),
        ),
        (
            "assistant",
            (
                f"{prefix}/gemini",
                f"{prefix}/grok",
                f"{prefix}/ia-agent",
            ),
        ),
    ]
    flags = current_flags()
    for feature, prefixes in rules:
        if flags.get(feature, True):
            continue
        if any(normalized == p or normalized.startswith(p + "/") for p in prefixes):
            return feature
    return None
