"""Helpers for constructing spans in tests without a full tracer pipeline.

:func:`build_span` produces a real, finished :class:`ReadableSpan` by driving
the OpenTelemetry SDK through an in-memory exporter. This keeps the golden
fixtures and unit tests exercising the same span objects instrumentation code
produces, rather than hand-rolled stand-ins.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import SpanKind

_KIND_BY_NAME = {
    "internal": SpanKind.INTERNAL,
    "server": SpanKind.SERVER,
    "client": SpanKind.CLIENT,
    "producer": SpanKind.PRODUCER,
    "consumer": SpanKind.CONSUMER,
}


def build_span(
    *,
    name: str,
    kind: str = "internal",
    attributes: Mapping[str, Any] | None = None,
) -> ReadableSpan:
    """Build and finish a single span, returning the exported ReadableSpan.

    Args:
        name: The span name.
        kind: One of ``internal``, ``server``, ``client``, ``producer``,
            ``consumer``.
        attributes: The span attributes.

    Returns:
        The finished :class:`ReadableSpan` as captured by the in-memory
        exporter.
    """

    span_kind = _KIND_BY_NAME[kind.lower()]
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("pytest-genai-semconv.testing")

    span = tracer.start_span(name, kind=span_kind)
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    span.end()
    provider.force_flush()

    finished = exporter.get_finished_spans()
    return finished[0]
