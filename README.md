# pytest-genai-semconv

Pytest assertions that verify emitted OpenTelemetry spans conform to the
OpenTelemetry **GenAI semantic conventions** (`gen_ai.*`).

Instrumentation libraries emit `gen_ai` spans; `pytest-genai-semconv` lets you
prove, in a unit or CI test, that those spans carry the right attributes, with
the right value types, and the right span kinds — before they reach a backend.

```python
from pytest_genai_semconv import assert_chat_span, assert_plan_span

def test_my_agent_emits_compliant_spans(genai_spans):
    run_my_agent()  # your code, instrumented with OpenTelemetry

    chat = genai_spans.spans_for_operation("chat")[0]
    assert_chat_span(chat, request_model="gpt-4")

    plan = genai_spans.spans_for_operation("plan")[0]
    assert_plan_span(plan, agent_name="research_agent")
```

## Installation

```bash
pip install pytest-genai-semconv
```

The package depends on `opentelemetry-api`, `opentelemetry-sdk`, and `pytest`.

## Relationship to the official OpenTelemetry GenAI conventions

The GenAI semantic conventions live in
[`open-telemetry/semantic-conventions-genai`](https://github.com/open-telemetry/semantic-conventions-genai).
That repository is the source of truth for the spec, and it also ships a
`reference/` project (`semconv-genai-reference`) that drives *real* LLM client
libraries against a mock server and validates the captured telemetry with
[OTel Weaver](https://github.com/open-telemetry/weaver), producing a
cross-library **compliance matrix**.

`pytest-genai-semconv` is complementary, not a replacement for that work:

| | `semantic-conventions-genai/reference/` | `pytest-genai-semconv` |
| --- | --- | --- |
| Purpose | Survey which real libraries emit which attributes | Assert *your own* spans in *your own* test suite |
| Mechanism | Runs scenarios against a mock server, validates via Weaver | In-process pytest assertions over captured spans |
| Consumed as | A repo tool run via `uv` scripts | A `pip install`-able pytest plugin |
| Audience | OTel maintainers / ecosystem reporting | Instrumentation and application authors writing CI tests |

In short: the upstream reference project answers *"which libraries comply?"*;
this package answers *"do the spans my code emits comply, and will my CI catch
it if that regresses?"* — a pytest-native check that is not currently packaged
for installation elsewhere.

## Quickstart

The package ships a pytest plugin that registers a `genai_spans` fixture. The
fixture installs an in-memory OpenTelemetry span exporter for the duration of a
single test and captures every span your instrumented code emits.

```python
from opentelemetry import trace

from pytest_genai_semconv import (
    assert_genai_span_compliant,
    assert_execute_tool_span,
)


def test_tool_span_is_compliant(genai_spans):
    tracer = trace.get_tracer("my-app")
    with tracer.start_as_current_span(
        "execute_tool get_weather",
        kind=trace.SpanKind.INTERNAL,
        attributes={
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": "get_weather",
        },
    ):
        ...

    span = genai_spans.finished_spans()[0]

    # Generic check: valid operation name, correct attribute types, required
    # attributes present.
    assert_genai_span_compliant(span)

    # Operation-specific check with an expected value.
    assert_execute_tool_span(span, tool_name="get_weather")
```

When a span is not compliant, the assertion fails with a message that names
every offending attribute:

```text
Span 'chat gpt-4' is not gen_ai-compliant:
  - missing required attribute gen_ai.provider.name for gen_ai.inference.client spans
  - gen_ai.usage.input_tokens must be an int, got str
```

## Public API

| Symbol | Purpose |
| --- | --- |
| `genai_spans` (fixture) | In-memory span exporter; `.finished_spans()`, `.spans_for_operation(name)`, `.clear()`. |
| `assert_genai_span_compliant(span)` | Generic gen_ai compliance check (all operations). |
| `assert_chat_span(span, *, request_model=None)` | `chat` inference span. |
| `assert_plan_span(span, *, agent_name=None)` | `plan` span (`gen_ai.plan.internal`, kind `INTERNAL`). |
| `assert_invoke_agent_span(span, *, agent_name=None)` | `invoke_agent` span (client requires `gen_ai.provider.name`). |
| `assert_execute_tool_span(span, *, tool_name=None)` | `execute_tool` span (requires `gen_ai.tool.name`). |
| `GenAISpanComplianceError` | Raised on any violation; exposes `.violations`. |

The assertions accept any span-like object exposing `name`, `kind`, and an
`attributes` mapping — exactly what the OpenTelemetry SDK in-memory exporter
returns, so they work directly on the fixture's captured spans.

## What is checked

For every span, `assert_genai_span_compliant` enforces:

- **`gen_ai.operation.name`** is present and is a well-known operation value.
- **Value types** — every recognised `gen_ai.*` attribute is type-checked
  against the convention registry (`int`, `double`, `boolean`, `string`,
  `string[]`); e.g. `gen_ai.usage.input_tokens` must be an `int`,
  `gen_ai.request.temperature` a number, `gen_ai.request.stream` a boolean.
- **Enumerated values** — `gen_ai.operation.name`, `gen_ai.output.type`,
  `gen_ai.provider.name`, and `gen_ai.token.type` must be well-known values.
- **Per-operation required attributes and span kind** for the operations with a
  defined span profile (see coverage below); e.g. `gen_ai.provider.name` on
  `chat`/`embeddings`/`create_agent` client spans, `gen_ai.tool.name` on
  `execute_tool` spans, and `INTERNAL` kind on `plan` spans.

Conditionally-required and recommended attributes are intentionally *not*
enforced as hard failures, matching the requirement levels in the spec.

### Span coverage

Type and enum checks apply to **all** recognised `gen_ai.*` attributes on any
span. Operation-specific *span profiles* (required attributes + allowed span
kind) are enforced for these operations:

| Operation | Span type | Profile enforced | Named helper |
| --- | --- | :---: | --- |
| `chat`, `text_completion`, `generate_content` | `gen_ai.inference.client` | ✅ | `assert_chat_span` (chat) |
| `embeddings` | `gen_ai.embeddings.client` | ✅ | — |
| `create_agent` | `gen_ai.create_agent.client` | ✅ | — |
| `invoke_agent` | `gen_ai.invoke_agent.client` / `.internal` | ✅ | `assert_invoke_agent_span` |
| `execute_tool` | `gen_ai.execute_tool.internal` | ✅ | `assert_execute_tool_span` |
| `invoke_workflow` | `gen_ai.invoke_workflow.internal` | ✅ | — |
| `plan` | `gen_ai.plan.internal` | ✅ | `assert_plan_span` |
| `retrieval`, memory operations | — | ⬜ (generic type/enum only) | — |

Operations without a span profile still get full attribute type and enum
validation; only their operation-specific required-attribute and span-kind
checks are not yet enforced. Extending profile coverage to `retrieval` and the
memory operations is tracked for a future release.

## Why this exists

The OpenTelemetry GenAI semantic conventions define how spans for LLM and agent
operations — `chat`, `embeddings`, `execute_tool`, `invoke_agent`,
`create_agent`, `invoke_workflow`, and `plan` — should be shaped. Instrumentation
libraries are responsible for emitting spans that follow those conventions.
Existing pytest tooling instruments code and captures spans; it does not check
that the captured spans match the `gen_ai` conventions, and the upstream
reference project validates *libraries* rather than offering an installable
assertion helper for your own suite.

`pytest-genai-semconv` fills that gap. It operationalizes the conventions as
executable assertions so instrumentation authors and application developers can
guard against silent drift as the spec evolves.

In particular, it supports the **`plan`** operation and the
`gen_ai.plan.internal` span, which represent an agent's planning / task
decomposition phase. A plan span wraps the decision phase where an agent
formulates a strategy before executing it; the LLM call that generates the plan
is a child of the plan span, and the resulting tool or task spans are siblings
under the same `invoke_agent` span. This library provides `assert_plan_span` to
verify those spans directly, along with golden multi-agent trajectory fixtures
that exercise `invoke_workflow` → `invoke_agent` → `plan` → `chat` →
`execute_tool` end to end.

## Attribute source of truth

The attribute names, value types, enum values, and per-operation requirements
are derived from the OpenTelemetry GenAI semantic conventions model files (see
`src/pytest_genai_semconv/spec.py` for the pinned source reference into
[`open-telemetry/semantic-conventions-genai`](https://github.com/open-telemetry/semantic-conventions-genai)).

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check src tests
ruff format --check src tests
```

## License

Apache-2.0. See [LICENSE](LICENSE).
