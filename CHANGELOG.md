# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

### Added

- Initial release.
- `assert_genai_span_compliant(span)` — generic validator that checks a span
  against the OpenTelemetry GenAI semantic conventions: presence and validity of
  `gen_ai.operation.name`, attribute value types, enumerated value membership
  (`gen_ai.operation.name`, `gen_ai.output.type`, `gen_ai.provider.name`,
  `gen_ai.token.type`), and per-operation required attributes.
- Operation-specific assertions: `assert_chat_span`, `assert_plan_span`,
  `assert_invoke_agent_span`, `assert_execute_tool_span`, each with optional
  value checks (e.g. `request_model`, `agent_name`, `tool_name`) and clear,
  attribute-naming failure messages.
- Support for the `plan` operation and the `gen_ai.plan.internal` span
  introduced in the OpenTelemetry GenAI semantic conventions.
- `genai_spans` pytest fixture (auto-registered via the `pytest11` entry point)
  built on the OpenTelemetry SDK `InMemorySpanExporter`, with
  `finished_spans()` and `spans_for_operation(name)` helpers.
- Golden example spans (valid and invalid) for every supported operation,
  including a full multi-agent trajectory
  (`invoke_workflow` → `invoke_agent` → `plan` → `chat` → `execute_tool`).

[Unreleased]: https://github.com/Krishnachaitanyakc/pytest-genai-semconv/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Krishnachaitanyakc/pytest-genai-semconv/releases/tag/v0.1.0
