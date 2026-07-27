import contextvars
import logging
import os
import structlog

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Context variables for structured logging
trace_id_cv = contextvars.ContextVar("trace_id", default=None)
tenant_id_cv = contextvars.ContextVar("tenant_id", default=None)
principal_id_cv = contextvars.ContextVar("principal_id", default=None)
matter_id_cv = contextvars.ContextVar("matter_id", default=None)
operation_id_cv = contextvars.ContextVar("operation_id", default=None)
job_id_cv = contextvars.ContextVar("job_id", default=None)


def add_contextvars(logger, method_name, event_dict):
    """Add contextvars to structured logs."""
    for key, cv in [
        ("trace_id", trace_id_cv),
        ("tenant_id", tenant_id_cv),
        ("principal_id", principal_id_cv),
        ("matter_id", matter_id_cv),
        ("operation_id", operation_id_cv),
        ("job_id", job_id_cv),
    ]:
        val = cv.get()
        if val is not None:
            event_dict[key] = val

    # Automatically attach active OpenTelemetry Trace ID if not already in event_dict
    if "trace_id" not in event_dict:
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            event_dict["trace_id"] = format(span.get_span_context().trace_id, "032x")

    return event_dict


def setup_structlog():
    """Configures structlog to output JSON with context variables."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def setup_opentelemetry(service_name: str = "mesa-law-api"):
    """Configures OpenTelemetry Tracing and Metrics."""
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    
    # Check if we are in testing to avoid OTLP overhead
    env = os.getenv("MESA_ENV", "development")
    if env == "test":
        return

    resource = Resource.create({"service.name": service_name})

    # Setup Tracing
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Setup Metrics
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)


# Define Custom Meters
def get_meter(name: str):
    return metrics.get_meter(name)

def setup_observability(app=None, service_name: str = "mesa-law-api"):
    """Initialize both Structlog and OpenTelemetry, and optionally instrument a FastAPI app."""
    setup_structlog()
    setup_opentelemetry(service_name)
    
    # Instrument HTTPX globally
    if not HTTPXClientInstrumentor().is_instrumented_by_opentelemetry:
        HTTPXClientInstrumentor().instrument()

    if app is not None:
        FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())
