"""Tests for the public assertion API.

Spans are constructed with the OpenTelemetry SDK, exported through the
in-memory exporter, and validated against the derived gen_ai spec.
"""

import pytest

from pytest_genai_semconv import (
    GenAISpanComplianceError,
    assert_chat_span,
    assert_execute_tool_span,
    assert_genai_span_compliant,
    assert_invoke_agent_span,
    assert_plan_span,
)
from pytest_genai_semconv.testing import build_span

# --------------------------------------------------------------------------
# Generic compliance
# --------------------------------------------------------------------------


def test_generic_valid_chat_span_passes() -> None:
    span = build_span(
        name="chat gpt-4",
        kind="client",
        attributes={
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "openai",
            "gen_ai.request.model": "gpt-4",
        },
    )
    assert_genai_span_compliant(span)


def test_missing_operation_name_fails() -> None:
    span = build_span(
        name="chat gpt-4",
        kind="client",
        attributes={"gen_ai.provider.name": "openai"},
    )
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(span)
    assert "gen_ai.operation.name" in str(exc.value)


def test_unknown_operation_name_fails() -> None:
    span = build_span(
        name="frobnicate gpt-4",
        kind="client",
        attributes={
            "gen_ai.operation.name": "frobnicate",
            "gen_ai.provider.name": "openai",
        },
    )
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(span)
    assert "frobnicate" in str(exc.value)


def test_wrong_attribute_type_fails() -> None:
    # gen_ai.usage.input_tokens must be an int per the registry.
    span = build_span(
        name="chat gpt-4",
        kind="client",
        attributes={
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "openai",
            "gen_ai.usage.input_tokens": "not-an-int",
        },
    )
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(span)
    assert "gen_ai.usage.input_tokens" in str(exc.value)


def test_invalid_provider_name_fails() -> None:
    span = build_span(
        name="chat gpt-4",
        kind="client",
        attributes={
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "not-a-real-provider",
        },
    )
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(span)
    assert "gen_ai.provider.name" in str(exc.value)


def test_invalid_output_type_fails() -> None:
    span = build_span(
        name="chat gpt-4",
        kind="client",
        attributes={
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "openai",
            "gen_ai.output.type": "hologram",
        },
    )
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(span)
    assert "gen_ai.output.type" in str(exc.value)


# --------------------------------------------------------------------------
# chat
# --------------------------------------------------------------------------


def test_assert_chat_span_passes() -> None:
    span = build_span(
        name="chat gpt-4",
        kind="client",
        attributes={
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "anthropic",
            "gen_ai.request.model": "claude-3",
        },
    )
    assert_chat_span(span)


def test_assert_chat_span_rejects_wrong_operation() -> None:
    span = build_span(
        name="plan",
        kind="internal",
        attributes={"gen_ai.operation.name": "plan"},
    )
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_chat_span(span)
    assert "chat" in str(exc.value)


def test_assert_chat_span_checks_expected_model() -> None:
    span = build_span(
        name="chat gpt-4",
        kind="client",
        attributes={
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "openai",
            "gen_ai.request.model": "gpt-4",
        },
    )
    assert_chat_span(span, request_model="gpt-4")
    with pytest.raises(GenAISpanComplianceError):
        assert_chat_span(span, request_model="gpt-5")


# --------------------------------------------------------------------------
# plan  (the operation authored in semantic-conventions-genai#97)
# --------------------------------------------------------------------------


def test_assert_plan_span_passes() -> None:
    span = build_span(
        name="plan research_agent",
        kind="internal",
        attributes={
            "gen_ai.operation.name": "plan",
            "gen_ai.agent.name": "research_agent",
        },
    )
    assert_plan_span(span)


def test_assert_plan_span_requires_operation_name() -> None:
    span = build_span(
        name="plan research_agent",
        kind="internal",
        attributes={"gen_ai.agent.name": "research_agent"},
    )
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_plan_span(span)
    assert "gen_ai.operation.name" in str(exc.value)


def test_assert_plan_span_checks_agent_name() -> None:
    span = build_span(
        name="plan research_agent",
        kind="internal",
        attributes={
            "gen_ai.operation.name": "plan",
            "gen_ai.agent.name": "research_agent",
        },
    )
    assert_plan_span(span, agent_name="research_agent")
    with pytest.raises(GenAISpanComplianceError):
        assert_plan_span(span, agent_name="other_agent")


def test_assert_plan_span_rejects_wrong_span_kind() -> None:
    # plan spans are INTERNAL per the spec.
    span = build_span(
        name="plan research_agent",
        kind="client",
        attributes={
            "gen_ai.operation.name": "plan",
            "gen_ai.agent.name": "research_agent",
        },
    )
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_plan_span(span)
    assert "INTERNAL" in str(exc.value)


def test_assert_plan_span_checks_span_name_prefix() -> None:
    span = build_span(
        name="do_the_thing",
        kind="internal",
        attributes={"gen_ai.operation.name": "plan"},
    )
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_plan_span(span)
    assert "span name" in str(exc.value).lower()


# --------------------------------------------------------------------------
# invoke_agent
# --------------------------------------------------------------------------


def test_assert_invoke_agent_span_passes_internal() -> None:
    span = build_span(
        name="invoke_agent research_agent",
        kind="internal",
        attributes={
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": "research_agent",
        },
    )
    assert_invoke_agent_span(span)


def test_assert_invoke_agent_span_client_requires_provider() -> None:
    # For CLIENT kind, gen_ai.provider.name is required.
    span = build_span(
        name="invoke_agent research_agent",
        kind="client",
        attributes={
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": "research_agent",
        },
    )
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_invoke_agent_span(span)
    assert "gen_ai.provider.name" in str(exc.value)


def test_assert_invoke_agent_span_client_passes_with_provider() -> None:
    span = build_span(
        name="invoke_agent research_agent",
        kind="client",
        attributes={
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.provider.name": "openai",
            "gen_ai.agent.name": "research_agent",
        },
    )
    assert_invoke_agent_span(span)


def test_assert_invoke_agent_span_checks_agent_name() -> None:
    span = build_span(
        name="invoke_agent research_agent",
        kind="internal",
        attributes={
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": "research_agent",
        },
    )
    with pytest.raises(GenAISpanComplianceError):
        assert_invoke_agent_span(span, agent_name="wrong")


# --------------------------------------------------------------------------
# execute_tool
# --------------------------------------------------------------------------


def test_assert_execute_tool_span_passes() -> None:
    span = build_span(
        name="execute_tool get_weather",
        kind="internal",
        attributes={
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": "get_weather",
        },
    )
    assert_execute_tool_span(span)


def test_assert_execute_tool_span_requires_tool_name() -> None:
    span = build_span(
        name="execute_tool get_weather",
        kind="internal",
        attributes={"gen_ai.operation.name": "execute_tool"},
    )
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_execute_tool_span(span)
    assert "gen_ai.tool.name" in str(exc.value)


def test_assert_execute_tool_span_checks_tool_name() -> None:
    span = build_span(
        name="execute_tool get_weather",
        kind="internal",
        attributes={
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": "get_weather",
        },
    )
    assert_execute_tool_span(span, tool_name="get_weather")
    with pytest.raises(GenAISpanComplianceError):
        assert_execute_tool_span(span, tool_name="send_email")


# --------------------------------------------------------------------------
# Multiple errors reported together
# --------------------------------------------------------------------------


def test_multiple_violations_reported_together() -> None:
    span = build_span(
        name="chat",
        kind="client",
        attributes={
            "gen_ai.operation.name": "chat",
            # missing provider.name, bad token type
            "gen_ai.usage.input_tokens": "oops",
        },
    )
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(span)
    message = str(exc.value)
    assert "gen_ai.provider.name" in message
    assert "gen_ai.usage.input_tokens" in message
