"""Optional OpenTelemetry integration with no-op fallback.

Provides init_tracing(), instrument_app(), get_tracer(), and a `trace()` decorator
that services and providers can use. If OpenTelemetry packages are not
installed this module provides safe no-op implementations so runtime works
without the instrumentation dependency.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry; fall back to no-op
try:
    from opentelemetry import trace as ot_trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    # Try OTLP exporters (http/grpc)
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as OTLP_SPAN_EXPORTER
    except ImportError:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as OTLP_SPAN_EXPORTER
        except ImportError:
            OTLP_SPAN_EXPORTER = None
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


def _parse_headers(headers_env: Optional[str], otlp_headers: Optional[dict]) -> Optional[dict]:
    """Parse OTLP headers from environment or use provided headers.

    Returns a dict of headers or None if none provided.
    """
    if otlp_headers:
        return otlp_headers
    if not headers_env:
        return None
    hdrs = {}
    for pair in headers_env.split(','):
        if '=' in pair:
            k, v = pair.split('=', 1)
            hdrs[k.strip()] = v.strip()
    return hdrs or None


def _instantiate_otlp_exporter(endpoint: str, headers: Optional[dict]):
    """Attempt to construct an OTLP exporter with endpoint and headers.

    Falls back to a no-arg constructor if the first attempt fails.
    """
    try:
        return OTLP_SPAN_EXPORTER(endpoint=endpoint, headers=headers)
    except Exception as exc:
        logger.exception("failed to instantiate OTLP_SPAN_EXPORTER with endpoint", exc_info=exc)
        try:
            return OTLP_SPAN_EXPORTER()
        except Exception as exc2:
            logger.exception("failed to instantiate OTLP_SPAN_EXPORTER without endpoint", exc_info=exc2)
            return None


def init_tracing(service_name: str = "genlogs", otlp_endpoint: Optional[str] = None, otlp_headers: Optional[dict] = None) -> None:
    """Initialize tracing pipeline when OpenTelemetry is available.

    Behavior:
    - If OTLP endpoint is provided (or OTEL_EXPORTER_OTLP_ENDPOINT env var), try to use OTLPSpanExporter.
    - Otherwise fall back to ConsoleSpanExporter for local visibility.
    - Uses a Resource with service.name set to service_name.
    """
    if not OTEL_AVAILABLE:
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    # Determine OTLP endpoint from parameter or env
    endpoint = otlp_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    headers_env = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
    headers = otlp_headers or None
    if headers_env and not headers:
        # headers are expected in the form key=val,key2=val2
        hdrs = {}
        for pair in headers_env.split(','):
            if '=' in pair:
                k, v = pair.split('=', 1)
                hdrs[k.strip()] = v.strip()
        headers = hdrs or None

    exporter = None
    if endpoint and OTLP_SPAN_EXPORTER is not None:
        exporter = _instantiate_otlp_exporter(endpoint, headers)

    if exporter is None:
        exporter = ConsoleSpanExporter()

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    ot_trace.set_tracer_provider(provider)


def instrument_app(app: Any, engine: Any = None) -> bool:
    """Apply automatic instrumentation for FastAPI, requests and SQLAlchemy.

    Returns True if instrumentation was applied, False otherwise.
    """
    if not OTEL_AVAILABLE:
        return False

    try:
        FastAPIInstrumentor().instrument_app(app)
    except Exception as exc:
        logger.exception("FastAPIInstrumentor.instrument_app failed", exc_info=exc)

    try:
        RequestsInstrumentor().instrument()
    except Exception as exc:
        logger.exception("RequestsInstrumentor.instrument failed", exc_info=exc)

    if engine is not None:
        try:
            # SQLAlchemyInstrumentor.instrument accepts engine argument in recent versions
            SQLAlchemyInstrumentor().instrument(engine=engine)
        except TypeError:
            try:
                # older API: provide engine directly
                SQLAlchemyInstrumentor().instrument()
            except Exception as exc:
                logger.debug("SQLAlchemyInstrumentor.instrument failed (old API)", exc_info=exc)
        except Exception as exc:
            logger.debug("SQLAlchemyInstrumentor.instrument failed", exc_info=exc)

    return True


def get_tracer(name: str):
    """Return a tracer-like object.

    If OTEL is unavailable, returns a no-op tracer that exposes
    start_as_current_span as a contextmanager.
    """
    if OTEL_AVAILABLE:
        return ot_trace.get_tracer(name)

    class _NoopSpanCtx:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def set_attribute(self, _key: str, _value: object) -> None:
            """No-op attribute setter for compatibility with real Span."""
            return None

    class _NoopTracer:
        @contextmanager
        def start_as_current_span(self, name: str):
            yield _NoopSpanCtx()

    return _NoopTracer()


def trace(span_name: str | None = None) -> Callable:
    """Decorator/context manager factory to trace function execution.

    Usage:
        @trace()
        def foo(...):
            ...
    """

    def decorator(fn: Callable) -> Callable:
        def wrapped(*args, **kwargs):
            tracer = get_tracer(fn.__module__)
            name = span_name or f"{fn.__module__}.{fn.__name__}"
            # tracer.start_as_current_span may be a contextmanager
            ctx = tracer.start_as_current_span(name)
            enter = getattr(ctx, "__enter__", None)
            _exit = getattr(ctx, "__exit__", None)
            if enter and _exit:
                enter()
                try:
                    return fn(*args, **kwargs)
                finally:
                    _exit(None, None, None)
            else:
                # If tracer.start_as_current_span is a contextmanager function
                with ctx:
                    return fn(*args, **kwargs)

        # Keep metadata
        try:
            wrapped.__name__ = fn.__name__
            wrapped.__doc__ = fn.__doc__
        except Exception as exc:
            logger.debug("failed to preserve metadata", exc_info=exc)
        return wrapped

    return decorator
