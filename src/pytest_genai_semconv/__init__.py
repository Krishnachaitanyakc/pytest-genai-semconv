"""pytest-genai-semconv: assert OpenTelemetry spans conform to the gen_ai
semantic conventions.

Public API:

- :func:`assert_genai_span_compliant` — generic compliance check.
- :func:`assert_chat_span`, :func:`assert_plan_span`,
  :func:`assert_invoke_agent_span`, :func:`assert_execute_tool_span` —
  operation-specific checks.
- :class:`GenAISpanComplianceError` — the assertion error type.
- The ``genai_spans`` pytest fixture (registered via the ``pytest11`` entry
  point) provides an in-memory span exporter.
"""

from .assertions import (
    GenAISpanComplianceError,
    assert_chat_span,
    assert_execute_tool_span,
    assert_genai_span_compliant,
    assert_invoke_agent_span,
    assert_plan_span,
)

__all__ = [
    "GenAISpanComplianceError",
    "assert_genai_span_compliant",
    "assert_chat_span",
    "assert_plan_span",
    "assert_invoke_agent_span",
    "assert_execute_tool_span",
    "__version__",
]

__version__ = "0.1.0"
