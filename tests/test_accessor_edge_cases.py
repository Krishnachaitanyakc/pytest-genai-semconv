"""Cover the tolerant span-accessor branches with minimal span stand-ins.

The assertions are documented to accept any object exposing ``name``,
``kind`` and ``attributes``. These tests exercise the degenerate shapes
(missing attributes, missing/opaque kind) that real spans never produce but
that the accessors defend against.
"""

from types import SimpleNamespace

import pytest

from pytest_genai_semconv import GenAISpanComplianceError, assert_genai_span_compliant
from pytest_genai_semconv.plugin import GenAISpanCollector


class _FakeExporter:
    def __init__(self, spans):
        self._spans = spans

    def get_finished_spans(self):
        return self._spans

    def clear(self):
        self._spans = []


def test_span_with_none_attributes_is_treated_as_empty() -> None:
    span = SimpleNamespace(name="x", kind=None, attributes=None)
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(span)
    assert "gen_ai.operation.name" in str(exc.value)


def test_span_with_opaque_kind_does_not_crash() -> None:
    # kind is a plain object without a ``name`` attribute -> falls back to str().
    span = SimpleNamespace(
        name="chat gpt-4",
        kind="client",  # plain string, no .name
        attributes={
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "openai",
        },
    )
    # "client".upper() == "CLIENT" which is an allowed kind for chat.
    assert_genai_span_compliant(span)


def test_collector_spans_for_operation_handles_missing_attributes() -> None:
    span_no_attrs = SimpleNamespace(name="x", kind=None, attributes=None)
    span_plan = SimpleNamespace(
        name="plan a",
        kind=None,
        attributes={"gen_ai.operation.name": "plan"},
    )
    collector = GenAISpanCollector(_FakeExporter([span_no_attrs, span_plan]))
    matches = collector.spans_for_operation("plan")
    assert matches == [span_plan]


def test_collector_clear_delegates_to_exporter() -> None:
    exporter = _FakeExporter([SimpleNamespace(name="x", kind=None, attributes={})])
    collector = GenAISpanCollector(exporter)
    collector.clear()
    assert collector.finished_spans() == ()


def test_span_with_none_kind_skips_kind_check() -> None:
    # A chat span with kind=None is otherwise compliant; the kind check is
    # simply not applied when the kind is unknown.
    span = SimpleNamespace(
        name="chat gpt-4",
        kind=None,
        attributes={
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "openai",
        },
    )
    assert_genai_span_compliant(span)


def test_unregistered_genai_attribute_is_not_type_checked() -> None:
    # A gen_ai.* key that is not in the registry snapshot is left alone.
    span = SimpleNamespace(
        name="chat gpt-4",
        kind="client",
        attributes={
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "openai",
            "gen_ai.some_future_attribute": 12345,
        },
    )
    assert_genai_span_compliant(span)


def test_any_typed_attribute_accepts_arbitrary_value() -> None:
    # gen_ai.tool.call.arguments has value type "any" in the registry.
    span = SimpleNamespace(
        name="execute_tool get_weather",
        kind="internal",
        attributes={
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": "get_weather",
            "gen_ai.tool.call.arguments": {"location": "Paris"},
        },
    )
    assert_genai_span_compliant(span)
