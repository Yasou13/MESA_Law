import contextvars
import logging
import os
import re
from functools import lru_cache
from typing import Any

import structlog
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Context variables for structured logging
request_id_cv: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
trace_id_cv: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "trace_id", default=None
)
tenant_id_cv: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "tenant_id", default=None
)
principal_id_cv: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "principal_id", default=None
)
matter_id_cv: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "matter_id", default=None
)
operation_id_cv: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "operation_id", default=None
)
job_id_cv: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "job_id", default=None
)
mutation_id_cv: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "mutation_id", default=None
)

_SENSITIVE_KEY_PARTS = (
    "authorization",
    "api_key",
    "apikey",
    "password",
    "secret",
    "token",
)
_CONTENT_KEYS = {
    "answer",
    "body",
    "document_content",
    "evidence_excerpt",
    "evidence_text",
    "file_bytes",
    "question",
    "text_content",
}
_BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+[^\s,;]+")
_DATABASE_URL_PATTERN = re.compile(
    r"(?i)(postgres(?:ql)?(?:\+[^:]+)?://)[^:@/]+:[^@/]+@"
)
_NAMED_SECRET_PATTERN = re.compile(
    r"(?i)(authorization|api[_-]?key|password|secret|token)(\s*[:=]\s*)([^\s,;}]+)"
)


def redact_log_text(value: str) -> str:
    """Remove common credential forms from a formatted log message."""
    value = _BEARER_PATTERN.sub("Bearer [REDACTED]", value)
    value = _DATABASE_URL_PATTERN.sub(r"\1[REDACTED]:[REDACTED]@", value)
    return _NAMED_SECRET_PATTERN.sub(r"\1\2[REDACTED]", value)


def _redact_value(key: str, value: Any) -> Any:
    normalized = key.lower()
    if normalized in _CONTENT_KEYS or any(
        part in normalized for part in _SENSITIVE_KEY_PARTS
    ):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {
            child_key: _redact_value(str(child_key), child)
            for child_key, child in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact_value(key, item) for item in value]
    if isinstance(value, bytes):
        return "[REDACTED_BYTES]"
    if isinstance(value, str):
        return redact_log_text(value)
    return value


def redact_event_dict(logger, method_name, event_dict):
    """Redact secrets and legal document content from structured events."""
    return {key: _redact_value(str(key), value) for key, value in event_dict.items()}


def setup_standard_logging_context() -> None:
    """Attach safe correlation fields to existing stdlib logging calls."""
    current_factory = logging.getLogRecordFactory()
    if getattr(current_factory, "_mesa_context_factory", False):
        return

    def context_factory(*args, **kwargs):
        record = current_factory(*args, **kwargs)
        message = redact_log_text(record.getMessage())
        record.args = ()
        context = {
            "request_id": request_id_cv.get(),
            "trace_id": trace_id_cv.get(),
            "job_id": job_id_cv.get(),
            "matter_id": matter_id_cv.get(),
            "mutation_id": mutation_id_cv.get(),
        }
        for key, value in context.items():
            setattr(record, key, value or "-")
        prefix = " ".join(
            f"{key}={value}" for key, value in context.items() if value is not None
        )
        record.msg = f"[{prefix}] {message}" if prefix else message
        return record

    context_factory._mesa_context_factory = True  # type: ignore[attr-defined]
    logging.setLogRecordFactory(context_factory)


def add_contextvars(logger, method_name, event_dict):
    """Add contextvars to structured logs."""
    for key, cv in [
        ("request_id", request_id_cv),
        ("trace_id", trace_id_cv),
        ("tenant_id", tenant_id_cv),
        ("principal_id", principal_id_cv),
        ("matter_id", matter_id_cv),
        ("operation_id", operation_id_cv),
        ("job_id", job_id_cv),
        ("mutation_id", mutation_id_cv),
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
            redact_event_dict,
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
    otlp_endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"
    )

    # Check if we are in testing to avoid OTLP overhead
    env = os.getenv("MESA_LAW_ENVIRONMENT", "development")
    enabled = os.getenv("MESA_LAW_OBSERVABILITY_ENABLED", "false").lower() in {
        "1",
        "true",
        "yes",
    }
    if env == "test" or not enabled:
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


@lru_cache(maxsize=32)
def _counter(name: str):
    return get_meter("mesa_law.operations").create_counter(name)


@lru_cache(maxsize=32)
def _histogram(name: str, unit: str):
    return get_meter("mesa_law.operations").create_histogram(name, unit=unit)


def increment_metric(
    name: str, *, attributes: dict[str, str] | None = None, amount: int = 1
) -> None:
    _counter(name).add(amount, attributes or {})


def record_metric(
    name: str,
    value: float,
    *,
    unit: str = "1",
    attributes: dict[str, str] | None = None,
) -> None:
    _histogram(name, unit).record(value, attributes or {})


def setup_observability(app=None, service_name: str = "mesa-law-api"):
    """Initialize both Structlog and OpenTelemetry, and optionally instrument a FastAPI app."""
    setup_standard_logging_context()
    setup_structlog()
    setup_opentelemetry(service_name)

    # Instrument HTTPX globally
    if not HTTPXClientInstrumentor().is_instrumented_by_opentelemetry:
        HTTPXClientInstrumentor().instrument()

    if app is not None:
        FastAPIInstrumentor.instrument_app(
            app, tracer_provider=trace.get_tracer_provider()
        )
