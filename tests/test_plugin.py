"""Tests for the pytest plugin fixture (in-memory span exporter)."""

from opentelemetry import trace

from pytest_genai_semconv import assert_chat_span, assert_plan_span


def test_genai_spans_fixture_captures_spans(genai_spans) -> None:
    tracer = trace.get_tracer("test")
    with tracer.start_as_current_span(
        "chat gpt-4",
        kind=trace.SpanKind.CLIENT,
        attributes={
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "openai",
            "gen_ai.request.model": "gpt-4",
        },
    ):
        pass

    spans = genai_spans.finished_spans()
    assert len(spans) == 1
    assert_chat_span(spans[0])


def test_genai_spans_fixture_is_isolated_between_tests(genai_spans) -> None:
    # This test must not see spans emitted by the previous test.
    assert genai_spans.finished_spans() == ()
    tracer = trace.get_tracer("test")
    with tracer.start_as_current_span(
        "plan agent",
        kind=trace.SpanKind.INTERNAL,
        attributes={
            "gen_ai.operation.name": "plan",
            "gen_ai.agent.name": "agent",
        },
    ):
        pass
    spans = genai_spans.finished_spans()
    assert len(spans) == 1
    assert_plan_span(spans[0])


def test_genai_spans_helper_get_by_operation(genai_spans) -> None:
    tracer = trace.get_tracer("test")
    with tracer.start_as_current_span(
        "invoke_agent research",
        kind=trace.SpanKind.INTERNAL,
        attributes={
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": "research",
        },
    ):
        with tracer.start_as_current_span(
            "plan research",
            kind=trace.SpanKind.INTERNAL,
            attributes={
                "gen_ai.operation.name": "plan",
                "gen_ai.agent.name": "research",
            },
        ):
            pass

    plan_spans = genai_spans.spans_for_operation("plan")
    assert len(plan_spans) == 1
    assert_plan_span(plan_spans[0])
