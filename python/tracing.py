"""
OpenTelemetry Distributed Tracing Configuration
================================================
Implements distributed tracing for SentinAL API using OpenTelemetry.
Exports via OTLP (gRPC) to any compatible backend (Jaeger, Grafana Tempo, etc.).

All opentelemetry imports are wrapped in try/except so the API starts
cleanly even when the optional packages are not installed.

Author: SentinAL Team
Date: 2026-01-24
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Graceful imports — tracing is optional; the API runs fine without it.
# ---------------------------------------------------------------------------
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
    _OTEL_CORE_AVAILABLE = True
except ImportError:
    _OTEL_CORE_AVAILABLE = False
    logger.debug("opentelemetry-sdk not installed — tracing disabled")

try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    _OTLP_AVAILABLE = True
except ImportError:
    _OTLP_AVAILABLE = False

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    _FASTAPI_INSTR = True
except ImportError:
    _FASTAPI_INSTR = False

try:
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    _REDIS_INSTR = True
except ImportError:
    _REDIS_INSTR = False

try:
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    _REQUESTS_INSTR = True
except ImportError:
    _REQUESTS_INSTR = False


def init_tracing(
    app,
    service_name: str = "sentinal-api",
    service_version: str = "2.0.0",
    sampling_rate: float = 1.0,
):
    """
    Initialize OpenTelemetry distributed tracing.

    Exports traces via OTLP (gRPC) to the endpoint configured by
    OTEL_EXPORTER_OTLP_ENDPOINT (default: http://localhost:4317).

    Args:
        app: FastAPI application instance
        service_name: Name of the service
        service_version: Version of the service
        sampling_rate: Trace sampling rate 0.0-1.0 (default: 1.0 = 100%)
    """
    tracing_enabled = os.getenv("TRACING_ENABLED", "false").lower() == "true"

    if not tracing_enabled:
        logger.info("Distributed tracing disabled (set TRACING_ENABLED=true to enable)")
        return None

    if not _OTEL_CORE_AVAILABLE:
        logger.warning(
            "opentelemetry-sdk not installed — tracing skipped. "
            "Run: pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc"
        )
        return None

    try:
        sampling_rate = float(os.getenv("TRACE_SAMPLING_RATE", str(sampling_rate)))
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

        resource = Resource(
            attributes={
                SERVICE_NAME: service_name,
                SERVICE_VERSION: service_version,
                "deployment.environment": os.getenv("ENVIRONMENT", "development"),
                "instance.id": os.getenv("INSTANCE_ID", "unknown"),
            }
        )

        sampler = TraceIdRatioBased(sampling_rate)
        provider = TracerProvider(resource=resource, sampler=sampler)

        if _OTLP_AVAILABLE:
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(f"✓ OTLP trace exporter → {otlp_endpoint}")
        else:
            logger.warning(
                "opentelemetry-exporter-otlp-proto-grpc not installed — "
                "traces will not be exported. "
                "Run: pip install opentelemetry-exporter-otlp-proto-grpc"
            )

        trace.set_tracer_provider(provider)

        if _FASTAPI_INSTR:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("✓ FastAPI instrumented for tracing")

        if _REDIS_INSTR:
            try:
                RedisInstrumentor().instrument()
                logger.info("✓ Redis instrumented for tracing")
            except Exception as e:
                logger.warning(f"Redis instrumentation failed: {e}")

        if _REQUESTS_INSTR:
            try:
                RequestsInstrumentor().instrument()
                logger.info("✓ HTTP requests instrumented for tracing")
            except Exception as e:
                logger.warning(f"Requests instrumentation failed: {e}")

        logger.info(
            f"✓ Distributed tracing initialized — "
            f"{service_name} v{service_version} @ {sampling_rate * 100}% sampling"
        )
        return provider

    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")
        logger.warning("Application will continue without distributed tracing")
        return None


def get_tracer(name: str = "sentinal"):
    """Get a tracer instance for creating custom spans."""
    if not _OTEL_CORE_AVAILABLE:
        return _NoOpTracer()
    return trace.get_tracer(name)


def create_span(name: str, attributes: Optional[dict] = None):
    """Create a custom span. Returns a no-op context manager if tracing is unavailable."""
    if not _OTEL_CORE_AVAILABLE:
        return _NoOpSpan()
    tracer = get_tracer()
    span = tracer.start_as_current_span(name)
    if attributes:
        with span as s:
            for key, value in attributes.items():
                s.set_attribute(key, value)
    return span


def set_span_attribute(key: str, value):
    """Set an attribute on the current span."""
    if not _OTEL_CORE_AVAILABLE:
        return
    span = trace.get_current_span()
    if span:
        span.set_attribute(key, value)


def set_span_error(exception: Exception):
    """Mark the current span as having an error."""
    if not _OTEL_CORE_AVAILABLE:
        return
    span = trace.get_current_span()
    if span:
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))
        span.record_exception(exception)


def get_trace_id() -> Optional[str]:
    """Get the current trace ID for log correlation."""
    if not _OTEL_CORE_AVAILABLE:
        return None
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return None


# ---------------------------------------------------------------------------
# No-op stubs used when opentelemetry packages are not installed
# ---------------------------------------------------------------------------
class _NoOpSpan:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def set_attribute(self, *args):
        pass


class _NoOpTracer:
    def start_as_current_span(self, *args, **kwargs):
        return _NoOpSpan()
    def start_span(self, *args, **kwargs):
        return _NoOpSpan()
