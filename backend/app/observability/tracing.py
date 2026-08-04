"""OpenTelemetry tracing preparation (collector optional)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import Tracer

from app.core.config import Settings

_PROVIDER_CONFIGURED = False


def configure_tracing(settings: Settings) -> TracerProvider | None:
    """
    Configure a TracerProvider.
    When OTEL_ENABLED is false, returns None and tracing remains a no-op.
    Does not require an external collector.
    """
    global _PROVIDER_CONFIGURED
    if not settings.OTEL_ENABLED:
        return None
    if _PROVIDER_CONFIGURED:
        return trace.get_tracer_provider()  # type: ignore[return-value]

    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.APP_ENV.value,
        }
    )
    provider = TracerProvider(resource=resource)
    if settings.OTEL_CONSOLE_EXPORT:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _PROVIDER_CONFIGURED = True
    return provider


def get_tracer(name: str = "edp") -> Tracer:
    return trace.get_tracer(name)


@contextmanager
def start_span(name: str, **attributes: str | int | float | bool) -> Iterator[None]:
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield
