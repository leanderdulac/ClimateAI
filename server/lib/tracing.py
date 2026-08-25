"""OpenTelemetry helpers. No-ops when tracing is disabled or the SDK is missing."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator, Optional

logger = logging.getLogger(__name__)


def get_tracer(name: str = "climatewise"):
    try:
        from opentelemetry import trace

        return trace.get_tracer(name)
    except Exception:
        return None


@contextmanager
def start_span(name: str, **attributes: Any) -> Iterator[Optional[Any]]:
    """Start a span and attach primitive attributes. Yields None if tracing is unavailable."""
    tracer = get_tracer()
    if tracer is None:
        yield None
        return

    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            if value is None:
                continue
            try:
                span.set_attribute(key, value)
            except Exception:
                span.set_attribute(key, str(value))
        try:
            yield span
        except Exception as exc:
            try:
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(exc).__name__)
                span.set_attribute("error.message", str(exc)[:500])
            except Exception:
                logger.debug("Failed to record span error attributes", exc_info=True)
            raise


def set_span_attributes(span: Optional[Any], **attributes: Any) -> None:
    if span is None:
        return
    for key, value in attributes.items():
        if value is None:
            continue
        try:
            span.set_attribute(key, value)
        except Exception:
            span.set_attribute(key, str(value))
