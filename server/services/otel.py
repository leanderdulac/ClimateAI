
import os
import logging

logger = logging.getLogger(__name__)




def init_otel(app):
    """Initialize OpenTelemetry tracing if enabled by env var OTEL_ENABLED=true."""
    if os.getenv("OTEL_ENABLED", "false").lower() != "true":
        logger.info("OpenTelemetry disabled (set OTEL_ENABLED=true to enable).")
        return

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")

    resource = Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "climateai-backend"),
            "service.version": os.getenv("OTEL_SERVICE_VERSION", "1.0.0"),
            "deployment.environment": os.getenv("ENV", "local"),
        }
    )

    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    LoggingInstrumentor().instrument(set_logging_format=True, tracer_provider=provider)
    logger.info(f"OpenTelemetry tracing enabled, exporting to {endpoint}")
