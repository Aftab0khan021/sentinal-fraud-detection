"""
OpenTelemetry Distributed Tracing Configuration
================================================
Implements distributed tracing for SentinAL API using OpenTelemetry and Jaeger.

Features:
- Automatic HTTP request tracing
- Custom span creation for business logic
- Trace context propagation
- Sampling configuration
- Integration with FastAPI, Redis, and HTTP clients

Author: SentinAL Team
Date: 2026-01-24
"""

import os
import logging
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

logger = logging.getLogger(__name__)


def init_tracing(
    app,
    service_name: str = "sentinal-api",
    service_version: str = "2.0.0",
    jaeger_host: Optional[str] = None,
    jaeger_port: Optional[int] = None,
    sampling_rate: float = 1.0
):
    """
    Initialize OpenTelemetry distributed tracing.
    
    Args:
        app: FastAPI application instance
        service_name: Name of the service
        service_version: Version of the service
        jaeger_host: Jaeger agent hostname (default: from env or 'jaeger')
        jaeger_port: Jaeger agent port (default: from env or 6831)
        sampling_rate: Trace sampling rate 0.0-1.0 (default: 1.0 = 100%)
    """
    
    # Get configuration from environment
    jaeger_host = jaeger_host or os.getenv("JAEGER_HOST", "jaeger")
    jaeger_port = jaeger_port or int(os.getenv("JAEGER_PORT", "6831"))
    sampling_rate = float(os.getenv("TRACE_SAMPLING_RATE", str(sampling_rate)))
    tracing_enabled = os.getenv("TRACING_ENABLED", "true").lower() == "true"
    
    if not tracing_enabled:
        logger.info("Distributed tracing is disabled")
        return None
    
    try:
        # Create resource with service information
        resource = Resource(attributes={
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
            "instance.id": os.getenv("INSTANCE_ID", "unknown")
        })
        
        # Set up Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_host,
            agent_port=jaeger_port,
        )
        
        # Configure tracer provider with sampling
        sampler = TraceIdRatioBased(sampling_rate)
        provider = TracerProvider(
            resource=resource,
            sampler=sampler
        )
        
        # Add batch span processor for better performance
        processor = BatchSpanProcessor(jaeger_exporter)
        provider.add_span_processor(processor)
        
        # Set as global tracer provider
        trace.set_tracer_provider(provider)
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        logger.info(f"✓ FastAPI instrumented for tracing")
        
        # Instrument Redis
        try:
            RedisInstrumentor().instrument()
            logger.info(f"✓ Redis instrumented for tracing")
        except Exception as e:
            logger.warning(f"Failed to instrument Redis: {e}")
        
        # Instrument HTTP requests
        try:
            RequestsInstrumentor().instrument()
            logger.info(f"✓ HTTP requests instrumented for tracing")
        except Exception as e:
            logger.warning(f"Failed to instrument HTTP requests: {e}")
        
        logger.info(f"✓ Distributed tracing initialized")
        logger.info(f"  Service: {service_name} v{service_version}")
        logger.info(f"  Jaeger: {jaeger_host}:{jaeger_port}")
        logger.info(f"  Sampling: {sampling_rate * 100}%")
        logger.info(f"  Instance: {os.getenv('INSTANCE_ID', 'unknown')}")
        
        return provider
        
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")
        logger.warning("Application will continue without distributed tracing")
        return None


def get_tracer(name: str = "sentinal"):
    """
    Get a tracer instance for creating custom spans.
    
    Args:
        name: Name of the tracer
        
    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


def create_span(name: str, attributes: Optional[dict] = None):
    """
    Create a custom span for tracing business logic.
    
    Usage:
        with create_span("fraud_detection", {"user_id": user_id}):
            # Your code here
            pass
    
    Args:
        name: Name of the span
        attributes: Optional attributes to add to the span
        
    Returns:
        Span context manager
    """
    tracer = get_tracer()
    span = tracer.start_as_current_span(name)
    
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    
    return span


def add_span_event(name: str, attributes: Optional[dict] = None):
    """
    Add an event to the current span.
    
    Args:
        name: Event name
        attributes: Optional event attributes
    """
    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes or {})


def set_span_attribute(key: str, value):
    """
    Set an attribute on the current span.
    
    Args:
        key: Attribute key
        value: Attribute value
    """
    span = trace.get_current_span()
    if span:
        span.set_attribute(key, value)


def set_span_error(exception: Exception):
    """
    Mark the current span as having an error.
    
    Args:
        exception: The exception that occurred
    """
    span = trace.get_current_span()
    if span:
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))
        span.record_exception(exception)


def get_trace_id() -> Optional[str]:
    """
    Get the current trace ID for correlation with logs.
    
    Returns:
        Trace ID as hex string, or None if no active span
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, '032x')
    return None
