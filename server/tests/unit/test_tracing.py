"""Pricing span helper."""

from lib.tracing import set_span_attributes, start_span


class _FakeSpan:
    def __init__(self):
        self.attrs = {}

    def set_attribute(self, key, value):
        self.attrs[key] = value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeTracer:
    def start_as_current_span(self, name):
        span = _FakeSpan()
        span.attrs["span.name"] = name
        return span


def test_start_span_records_attributes(monkeypatch):
    fake = _FakeTracer()
    monkeypatch.setattr("lib.tracing.get_tracer", lambda name="climatewise": fake)
    with start_span("pricing.quote", **{"pricing.kind": "policy_quote"}) as span:
        assert span is not None
        set_span_attributes(span, **{"pricing.status": "APPROVED"})
        assert span.attrs["pricing.kind"] == "policy_quote"
        assert span.attrs["pricing.status"] == "APPROVED"


def test_start_span_is_noop_without_tracer(monkeypatch):
    monkeypatch.setattr("lib.tracing.get_tracer", lambda name="climatewise": None)
    with start_span("pricing.quote") as span:
        assert span is None
        set_span_attributes(span, pricing_status="x")
