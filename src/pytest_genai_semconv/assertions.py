"""Assertions that verify OpenTelemetry spans conform to the gen_ai
semantic conventions.

The assertions accept any span-like object exposing the read-only interface of
:class:`opentelemetry.sdk.trace.ReadableSpan` — that is, a ``name`` attribute, a
``kind`` attribute, and an ``attributes`` mapping. This is exactly what the
in-memory span exporter returns.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from . import spec


class GenAISpanComplianceError(AssertionError):
    """Raised when a span violates the gen_ai semantic conventions.

    Carries the list of individual violation messages so callers can inspect
    them programmatically in addition to reading the formatted message.
    """

    def __init__(self, span_name: str, violations: Sequence[str]) -> None:
        self.span_name = span_name
        self.violations = list(violations)
        body = "\n".join(f"  - {v}" for v in self.violations)
        super().__init__(f"Span {span_name!r} is not gen_ai-compliant:\n{body}")


# ---------------------------------------------------------------------------
# Span accessors (tolerant of both SDK ReadableSpan and simple stand-ins)
# ---------------------------------------------------------------------------


def _span_name(span: Any) -> str:
    return getattr(span, "name", "<unnamed>")


def _span_attributes(span: Any) -> Mapping[str, Any]:
    attributes = getattr(span, "attributes", None)
    if attributes is None:
        return {}
    return attributes


def _span_kind_name(span: Any) -> str | None:
    kind = getattr(span, "kind", None)
    if kind is None:
        return None
    # opentelemetry SpanKind is an IntEnum whose ``name`` is CLIENT/INTERNAL/...
    name = getattr(kind, "name", None)
    if isinstance(name, str):
        return name.upper()
    return str(kind).upper()


# ---------------------------------------------------------------------------
# Type checking against the registry value types
# ---------------------------------------------------------------------------


def _type_violation(key: str, value: Any) -> str | None:
    """Return a violation message if ``value`` does not match the spec type."""

    expected = spec.ATTRIBUTE_TYPES.get(key)
    if expected is None:
        return None  # unknown gen_ai attribute; nothing to check here
    if expected == "any":
        return None
    if expected == "string":
        if not isinstance(value, str):
            return f"{key} must be a string, got {type(value).__name__}"
        return None
    if expected == "int":
        # bool is a subclass of int but is not a valid int-typed attribute.
        if isinstance(value, bool) or not isinstance(value, int):
            return f"{key} must be an int, got {type(value).__name__}"
        return None
    if expected == "double":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"{key} must be a number (double), got {type(value).__name__}"
        return None
    if expected == "boolean":
        if not isinstance(value, bool):
            return f"{key} must be a boolean, got {type(value).__name__}"
        return None
    if expected == "string[]":
        if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
            return f"{key} must be an array of strings, got {type(value).__name__}"
        if not all(isinstance(item, str) for item in value):
            return f"{key} must contain only strings"
        return None
    return None  # pragma: no cover - defensive: all spec types handled above


def _enum_violation(key: str, value: Any) -> str | None:
    allowed = spec.ENUM_ATTRIBUTES.get(key)
    if allowed is None:
        return None
    if value not in allowed:
        sample = ", ".join(sorted(allowed)[:6])
        return (
            f"{key} has invalid value {value!r}; expected one of the "
            f"well-known values (e.g. {sample}, ...)"
        )
    return None


# ---------------------------------------------------------------------------
# Core collectors
# ---------------------------------------------------------------------------


def _collect_generic_violations(span: Any) -> list[str]:
    """Violations that apply to any gen_ai span, independent of operation."""

    attributes = _span_attributes(span)
    violations: list[str] = []

    operation = attributes.get("gen_ai.operation.name")
    if operation is None:
        violations.append("missing required attribute gen_ai.operation.name")

    # Type and enum checks for every recognised gen_ai attribute present.
    for key, value in attributes.items():
        if not str(key).startswith("gen_ai."):
            continue
        type_msg = _type_violation(str(key), value)
        if type_msg:
            violations.append(type_msg)
            continue  # skip enum check when the type is already wrong
        enum_msg = _enum_violation(str(key), value)
        if enum_msg:
            violations.append(enum_msg)

    return violations


def _resolve_profile(span: Any) -> spec.SpanProfile | None:
    operation = _span_attributes(span).get("gen_ai.operation.name")
    if operation == "invoke_agent":
        kind = _span_kind_name(span) or spec.SPAN_KIND_INTERNAL
        return spec.invoke_agent_profile(kind)
    if isinstance(operation, str):
        return spec.profile_for_operation(operation)
    return None


def _collect_profile_violations(
    span: Any,
    profile: spec.SpanProfile,
    *,
    check_kind: bool = True,
    check_span_name: bool = False,
) -> list[str]:
    attributes = _span_attributes(span)
    violations: list[str] = []

    for key in profile.required_attributes:
        if attributes.get(key) is None:
            violations.append(
                f"missing required attribute {key} for {profile.span_type} spans"
            )

    if check_kind and profile.allowed_kinds:
        kind = _span_kind_name(span)
        if kind is not None and kind not in profile.allowed_kinds:
            expected = " or ".join(profile.allowed_kinds)
            violations.append(
                f"span kind must be {expected} for {profile.span_type} "
                f"spans, got {kind}"
            )

    if check_span_name and profile.span_name_prefix is not None:
        name = _span_name(span)
        prefix = profile.span_name_prefix
        if not (name == prefix or name.startswith(prefix + " ")):
            violations.append(
                f"span name {name!r} should start with "
                f"{profile.span_name_prefix!r} for {profile.span_type} spans"
            )

    return violations


# ---------------------------------------------------------------------------
# Public assertions
# ---------------------------------------------------------------------------


def assert_genai_span_compliant(span: Any) -> None:
    """Assert that ``span`` conforms to the gen_ai semantic conventions.

    Checks that ``gen_ai.operation.name`` is present and a well-known value,
    that every recognised gen_ai attribute has the correct value type and (for
    enumerated attributes) a well-known value, and that the operation-specific
    required attributes are present.

    Raises:
        GenAISpanComplianceError: if any violation is found. The error message
            names every offending attribute.
    """

    violations = _collect_generic_violations(span)

    profile = _resolve_profile(span)
    if profile is not None:
        violations.extend(_collect_profile_violations(span, profile, check_kind=True))

    if violations:
        raise GenAISpanComplianceError(_span_name(span), violations)


def _assert_operation(
    span: Any,
    expected_operation: str,
    *,
    check_span_name: bool,
    expected_values: Mapping[str, Any] | None = None,
) -> None:
    attributes = _span_attributes(span)
    violations: list[str] = []

    operation = attributes.get("gen_ai.operation.name")
    if operation != expected_operation:
        violations.append(
            f"gen_ai.operation.name must be {expected_operation!r}, got {operation!r}"
        )

    # Generic checks (types, enums, presence of operation.name).
    violations.extend(_collect_generic_violations(span))

    # Operation profile checks.
    if operation == "invoke_agent":
        profile = spec.invoke_agent_profile(
            _span_kind_name(span) or spec.SPAN_KIND_INTERNAL
        )
    else:
        profile = spec.profile_for_operation(expected_operation)
    if profile is not None:
        violations.extend(
            _collect_profile_violations(
                span,
                profile,
                check_kind=True,
                check_span_name=check_span_name,
            )
        )

    if expected_values:
        for key, expected in expected_values.items():
            if expected is None:
                continue
            actual = attributes.get(key)
            if actual != expected:
                violations.append(f"{key} must equal {expected!r}, got {actual!r}")

    # Deduplicate while preserving order (generic + profile can overlap).
    seen: set[str] = set()
    unique: list[str] = []
    for message in violations:
        if message not in seen:
            seen.add(message)
            unique.append(message)

    if unique:
        raise GenAISpanComplianceError(_span_name(span), unique)


def assert_chat_span(span: Any, *, request_model: str | None = None) -> None:
    """Assert that ``span`` is a compliant ``chat`` inference span.

    Args:
        span: The span to validate.
        request_model: If given, ``gen_ai.request.model`` must equal this.
    """

    _assert_operation(
        span,
        "chat",
        check_span_name=False,
        expected_values={"gen_ai.request.model": request_model},
    )


def assert_plan_span(span: Any, *, agent_name: str | None = None) -> None:
    """Assert that ``span`` is a compliant ``plan`` span.

    The ``plan`` operation (``gen_ai.plan.internal`` span) was introduced in
    semantic-conventions-genai#97 to represent an agent's planning / task
    decomposition phase. The span kind MUST be ``INTERNAL`` and the span name
    SHOULD start with ``plan``.

    Args:
        span: The span to validate.
        agent_name: If given, ``gen_ai.agent.name`` must equal this.
    """

    _assert_operation(
        span,
        "plan",
        check_span_name=True,
        expected_values={"gen_ai.agent.name": agent_name},
    )


def assert_invoke_agent_span(span: Any, *, agent_name: str | None = None) -> None:
    """Assert that ``span`` is a compliant ``invoke_agent`` span.

    For ``CLIENT`` spans, ``gen_ai.provider.name`` is required; for
    ``INTERNAL`` spans it is not.

    Args:
        span: The span to validate.
        agent_name: If given, ``gen_ai.agent.name`` must equal this.
    """

    _assert_operation(
        span,
        "invoke_agent",
        check_span_name=False,
        expected_values={"gen_ai.agent.name": agent_name},
    )


def assert_execute_tool_span(span: Any, *, tool_name: str | None = None) -> None:
    """Assert that ``span`` is a compliant ``execute_tool`` span.

    ``gen_ai.tool.name`` is required.

    Args:
        span: The span to validate.
        tool_name: If given, ``gen_ai.tool.name`` must equal this.
    """

    _assert_operation(
        span,
        "execute_tool",
        check_span_name=False,
        expected_values={"gen_ai.tool.name": tool_name},
    )
