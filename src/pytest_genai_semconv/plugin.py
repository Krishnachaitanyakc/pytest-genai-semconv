"""pytest plugin exposing an in-memory gen_ai span capture fixture.

The ``genai_spans`` fixture installs a fresh :class:`TracerProvider` backed by
an :class:`InMemorySpanExporter` as the global OpenTelemetry tracer provider for
the duration of a single test, then restores the previous provider. Spans
emitted by code under test (through ``opentelemetry.trace.get_tracer``) are
captured and exposed through a small, ergonomic handle.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)


class GenAISpanCollector:
    """Ergonomic accessor over captured spans."""

    def __init__(self, exporter: InMemorySpanExporter) -> None:
        self._exporter = exporter

    def finished_spans(self) -> tuple[ReadableSpan, ...]:
        """Return all finished spans captured so far, in export order."""

        return tuple(self._exporter.get_finished_spans())

    def spans_for_operation(self, operation_name: str) -> list[ReadableSpan]:
        """Return finished spans whose ``gen_ai.operation.name`` matches."""

        result: list[ReadableSpan] = []
        for span in self.finished_spans():
            attributes = span.attributes or {}
            if attributes.get("gen_ai.operation.name") == operation_name:
                result.append(span)
        return result

    def clear(self) -> None:
        """Discard all captured spans."""

        self._exporter.clear()


def _reset_tracer_provider(provider: Any) -> None:
    # opentelemetry guards against overriding the global provider more than once
    # (via a ``Once`` sentinel), so per-test isolation requires resetting that
    # guard before installing a fresh provider. This mirrors the approach used
    # by OpenTelemetry's own test suite. The private-attribute access is guarded
    # so the plugin fails loudly with a clear message if the internals change.
    try:
        trace._TRACER_PROVIDER_SET_ONCE._done = False  # type: ignore[attr-defined]
        trace._TRACER_PROVIDER = provider  # type: ignore[attr-defined]
    except AttributeError as exc:  # pragma: no cover - version-guard
        raise RuntimeError(
            "pytest-genai-semconv could not reset the global OpenTelemetry tracer "
            "provider for test isolation; the installed opentelemetry-api "
            "version may be incompatible with this plugin."
        ) from exc


@pytest.fixture
def genai_spans() -> Iterator[GenAISpanCollector]:
    """Capture gen_ai spans emitted during a test via an in-memory exporter."""

    previous_provider = trace._TRACER_PROVIDER  # type: ignore[attr-defined]

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    _reset_tracer_provider(provider)
    try:
        yield GenAISpanCollector(exporter)
    finally:
        provider.force_flush()
        provider.shutdown()
        _reset_tracer_provider(previous_provider)
