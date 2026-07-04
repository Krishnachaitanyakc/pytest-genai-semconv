"""Exhaustive coverage of attribute value-type validation and edge cases."""

import pytest

from pytest_genai_semconv import (
    GenAISpanComplianceError,
    assert_genai_span_compliant,
    spec,
)
from pytest_genai_semconv.testing import build_span


def _chat(**extra):
    attrs = {"gen_ai.operation.name": "chat", "gen_ai.provider.name": "openai"}
    attrs.update(extra)
    return build_span(name="chat gpt-4", kind="client", attributes=attrs)


# --- string[] validation ---------------------------------------------------


def test_string_array_accepts_list_of_strings() -> None:
    assert_genai_span_compliant(
        _chat(**{"gen_ai.request.stop_sequences": ["stop", "end"]})
    )


def test_string_array_rejects_bare_string() -> None:
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(_chat(**{"gen_ai.request.stop_sequences": "stop"}))
    assert "gen_ai.request.stop_sequences" in str(exc.value)


def test_string_array_rejects_non_string_items() -> None:
    # OTel coerces mixed sequences; validate the message name is surfaced.
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(
            _chat(**{"gen_ai.response.finish_reasons": [1, 2, 3]})
        )
    assert "gen_ai.response.finish_reasons" in str(exc.value)


# --- double validation -----------------------------------------------------


def test_double_accepts_int() -> None:
    assert_genai_span_compliant(_chat(**{"gen_ai.request.temperature": 1}))


def test_double_rejects_bool() -> None:
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(_chat(**{"gen_ai.request.temperature": True}))
    assert "gen_ai.request.temperature" in str(exc.value)


# --- int validation --------------------------------------------------------


def test_int_rejects_bool() -> None:
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(_chat(**{"gen_ai.request.max_tokens": True}))
    assert "gen_ai.request.max_tokens" in str(exc.value)


# --- boolean validation ----------------------------------------------------


def test_boolean_accepts_bool() -> None:
    assert_genai_span_compliant(_chat(**{"gen_ai.request.stream": True}))


def test_boolean_rejects_int() -> None:
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(_chat(**{"gen_ai.request.stream": 1}))
    assert "gen_ai.request.stream" in str(exc.value)


# --- string validation -----------------------------------------------------


def test_string_rejects_int() -> None:
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(_chat(**{"gen_ai.response.id": 123}))
    assert "gen_ai.response.id" in str(exc.value)


# --- non-gen_ai attributes are ignored -------------------------------------


def test_non_genai_attributes_are_ignored() -> None:
    # A conventional non-gen_ai attribute with any type must not trip the check.
    assert_genai_span_compliant(_chat(**{"server.address": "api.openai.com"}))


# --- spans with no attributes ----------------------------------------------


def test_span_with_no_attributes_fails_on_operation_name() -> None:
    span = build_span(name="mystery", kind="internal")
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(span)
    assert "gen_ai.operation.name" in str(exc.value)


# --- unknown operation name yields no profile (branch coverage) -------------


def test_unknown_operation_has_no_profile_but_still_flags_enum() -> None:
    span = build_span(
        name="weird",
        kind="internal",
        attributes={"gen_ai.operation.name": "weird"},
    )
    with pytest.raises(GenAISpanComplianceError) as exc:
        assert_genai_span_compliant(span)
    assert "gen_ai.operation.name" in str(exc.value)


# --- spec helper branches --------------------------------------------------


def test_profile_for_operation_invoke_agent_returns_internal_default() -> None:
    profile = spec.profile_for_operation("invoke_agent")
    assert profile is not None
    assert profile.span_type == "gen_ai.invoke_agent.internal"


def test_profile_for_operation_unknown_returns_none() -> None:
    assert spec.profile_for_operation("definitely_not_an_operation") is None
