"""Golden-fixture tests: every valid example must pass compliance and every
invalid example must fail it, including plan / agent / workflow trajectories."""

import pytest

from pytest_genai_semconv import GenAISpanComplianceError, assert_genai_span_compliant
from pytest_genai_semconv.golden import (
    INVALID_SPANS,
    VALID_SPANS,
    load_span,
)


@pytest.mark.parametrize("name", sorted(VALID_SPANS))
def test_valid_golden_spans_pass(name: str) -> None:
    span = load_span(VALID_SPANS[name])
    assert_genai_span_compliant(span)


@pytest.mark.parametrize("name", sorted(INVALID_SPANS))
def test_invalid_golden_spans_fail(name: str) -> None:
    span = load_span(INVALID_SPANS[name])
    with pytest.raises(GenAISpanComplianceError):
        assert_genai_span_compliant(span)


def test_golden_covers_plan_agent_and_workflow() -> None:
    # The trajectory cases the package is meant to operationalize must exist.
    for key in ("plan", "invoke_agent", "invoke_workflow", "execute_tool", "chat"):
        assert any(key in name for name in VALID_SPANS), f"missing valid {key}"
    for key in ("plan", "invoke_agent", "invoke_workflow"):
        assert any(key in name for name in INVALID_SPANS), f"missing invalid {key}"


def test_full_agent_trajectory_all_compliant() -> None:
    # A realistic multi-agent trajectory: workflow -> invoke_agent -> plan ->
    # chat -> execute_tool. Every span in it should be individually compliant.
    from pytest_genai_semconv.golden import AGENT_TRAJECTORY

    spans = [load_span(descriptor) for descriptor in AGENT_TRAJECTORY]
    assert len(spans) >= 5
    for span in spans:
        assert_genai_span_compliant(span)
