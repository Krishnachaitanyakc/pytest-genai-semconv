"""Tests for the embedded gen_ai semantic-convention spec metadata.

These verify that the spec table the validator relies on matches the values
derived from the live OpenTelemetry GenAI semantic conventions
(open-telemetry/semantic-conventions-genai, model/gen-ai/registry.yaml and
model/gen-ai/spans.yaml).
"""

from pytest_genai_semconv import spec


def test_operation_names_include_plan() -> None:
    # The `plan` operation was added in semantic-conventions-genai#97.
    assert "plan" in spec.OPERATION_NAMES


def test_operation_names_match_registry() -> None:
    expected = {
        "chat",
        "generate_content",
        "text_completion",
        "embeddings",
        "retrieval",
        "create_agent",
        "invoke_agent",
        "execute_tool",
        "invoke_workflow",
        "plan",
        "search_memory",
        "create_memory",
        "update_memory",
        "upsert_memory",
        "delete_memory",
        "create_memory_store",
        "delete_memory_store",
    }
    assert expected <= spec.OPERATION_NAMES


def test_output_type_values() -> None:
    assert spec.OUTPUT_TYPES == {"text", "json", "image", "speech"}


def test_provider_names_include_core_providers() -> None:
    for provider in ("openai", "anthropic", "aws.bedrock", "azure.ai.inference"):
        assert provider in spec.PROVIDER_NAMES


def test_attribute_types_cover_core_keys() -> None:
    assert spec.ATTRIBUTE_TYPES["gen_ai.operation.name"] == "string"
    assert spec.ATTRIBUTE_TYPES["gen_ai.usage.input_tokens"] == "int"
    assert spec.ATTRIBUTE_TYPES["gen_ai.request.temperature"] == "double"
    assert spec.ATTRIBUTE_TYPES["gen_ai.request.stop_sequences"] == "string[]"
    assert spec.ATTRIBUTE_TYPES["gen_ai.request.stream"] == "boolean"


def test_plan_operation_maps_to_plan_span() -> None:
    profile = spec.profile_for_operation("plan")
    assert profile is not None
    assert profile.span_type == "gen_ai.plan.internal"
    assert "gen_ai.operation.name" in profile.required_attributes


def test_execute_tool_requires_tool_name() -> None:
    profile = spec.profile_for_operation("execute_tool")
    assert profile is not None
    assert "gen_ai.tool.name" in profile.required_attributes


def test_chat_requires_provider_name() -> None:
    profile = spec.profile_for_operation("chat")
    assert profile is not None
    assert "gen_ai.provider.name" in profile.required_attributes
    assert "gen_ai.operation.name" in profile.required_attributes
