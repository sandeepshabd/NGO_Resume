from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI


_provider_initialized = False
_httpx_instrumented = False
_requests_instrumented = False
_instrumented_apps: set[int] = set()


def init_tracing(service_name: str, app: FastAPI | None = None) -> None:
    """Initialize OpenTelemetry tracing and instrument app/client libraries.

    Tracing can be disabled with OTEL_TRACING_ENABLED=false.
    """
    if os.getenv("OTEL_TRACING_ENABLED", "true").lower() in {"0", "false", "no"}:
        return

    otel = _import_otel()
    if otel is None:
        return

    global _provider_initialized, _httpx_instrumented, _requests_instrumented

    if not _provider_initialized:
        resource = otel["Resource"].create(
            {
                "service.name": service_name,
                "service.namespace": "skillbridge",
            }
        )
        sample_ratio = _sample_ratio()
        sampler = otel["ParentBased"](otel["TraceIdRatioBased"](sample_ratio))
        provider = otel["TracerProvider"](resource=resource, sampler=sampler)
        provider.add_span_processor(
            otel["BatchSpanProcessor"](otel["CloudTraceSpanExporter"]())
        )
        otel["trace"].set_tracer_provider(provider)
        _provider_initialized = True

    if not _httpx_instrumented:
        otel["HTTPXClientInstrumentor"]().instrument()
        _httpx_instrumented = True

    if not _requests_instrumented and otel["RequestsInstrumentor"] is not None:
        otel["RequestsInstrumentor"]().instrument()
        _requests_instrumented = True

    if app is not None and id(app) not in _instrumented_apps:
        excluded_urls = os.getenv("OTEL_EXCLUDED_URLS", "/healthz,/readyz")
        otel["FastAPIInstrumentor"]().instrument_app(app, excluded_urls=excluded_urls)
        _instrumented_apps.add(id(app))


def _sample_ratio() -> float:
    raw_value = os.getenv("OTEL_TRACES_SAMPLER_ARG", "1.0")
    try:
        ratio = float(raw_value)
    except ValueError:
        return 1.0
    return max(0.0, min(1.0, ratio))


def _import_otel() -> dict[str, Any] | None:
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
    except ImportError:
        return None

    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
    except ImportError:
        RequestsInstrumentor = None

    return {
        "trace": trace,
        "CloudTraceSpanExporter": CloudTraceSpanExporter,
        "FastAPIInstrumentor": FastAPIInstrumentor,
        "HTTPXClientInstrumentor": HTTPXClientInstrumentor,
        "RequestsInstrumentor": RequestsInstrumentor,
        "Resource": Resource,
        "TracerProvider": TracerProvider,
        "BatchSpanProcessor": BatchSpanProcessor,
        "ParentBased": ParentBased,
        "TraceIdRatioBased": TraceIdRatioBased,
    }