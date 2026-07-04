"""Golden example spans for gen_ai operations.

Each descriptor is a plain dict that :func:`load_span` turns into a real
finished ``ReadableSpan`` (via the OpenTelemetry SDK in-memory exporter). Valid
descriptors are expected to pass :func:`assert_genai_span_compliant`; invalid
descriptors are expected to fail it. Coverage includes chat, embeddings,
create_agent, invoke_agent, execute_tool, invoke_workflow, and the ``plan``
operation, plus a full multi-agent trajectory.
"""

from __future__ import annotations

from typing import Any

from opentelemetry.sdk.trace import ReadableSpan

from .testing import build_span

SpanDescriptor = dict[str, Any]


def load_span(descriptor: SpanDescriptor) -> ReadableSpan:
    """Materialise a golden span descriptor into a finished ReadableSpan."""

    return build_span(
        name=descriptor["name"],
        kind=descriptor.get("kind", "internal"),
        attributes=descriptor.get("attributes", {}),
    )


# ---------------------------------------------------------------------------
# Valid golden spans
# ---------------------------------------------------------------------------

VALID_SPANS: dict[str, SpanDescriptor] = {
    "chat_openai": {
        "name": "chat gpt-4",
        "kind": "client",
        "attributes": {
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "openai",
            "gen_ai.request.model": "gpt-4",
            "gen_ai.request.temperature": 0.7,
            "gen_ai.request.max_tokens": 256,
            "gen_ai.usage.input_tokens": 42,
            "gen_ai.usage.output_tokens": 128,
            "gen_ai.response.finish_reasons": ["stop"],
            "gen_ai.output.type": "text",
        },
    },
    "chat_anthropic": {
        "name": "chat claude-3-5-sonnet",
        "kind": "client",
        "attributes": {
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "anthropic",
            "gen_ai.request.model": "claude-3-5-sonnet",
            "gen_ai.usage.input_tokens": 100,
            "gen_ai.usage.output_tokens": 200,
        },
    },
    "embeddings": {
        "name": "embeddings text-embedding-3-small",
        "kind": "client",
        "attributes": {
            "gen_ai.operation.name": "embeddings",
            "gen_ai.provider.name": "openai",
            "gen_ai.request.model": "text-embedding-3-small",
            "gen_ai.request.encoding_formats": ["float"],
            "gen_ai.embeddings.dimension.count": 1536,
            "gen_ai.usage.input_tokens": 8,
        },
    },
    "create_agent": {
        "name": "create_agent research_agent",
        "kind": "client",
        "attributes": {
            "gen_ai.operation.name": "create_agent",
            "gen_ai.provider.name": "openai",
            "gen_ai.agent.name": "research_agent",
            "gen_ai.agent.description": "Researches topics and drafts reports",
            "gen_ai.request.model": "gpt-4",
        },
    },
    "invoke_agent_internal": {
        "name": "invoke_agent research_agent",
        "kind": "internal",
        "attributes": {
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": "research_agent",
            "gen_ai.request.model": "gpt-4",
        },
    },
    "invoke_agent_client": {
        "name": "invoke_agent research_agent",
        "kind": "client",
        "attributes": {
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.provider.name": "openai",
            "gen_ai.agent.name": "research_agent",
        },
    },
    "execute_tool": {
        "name": "execute_tool get_weather",
        "kind": "internal",
        "attributes": {
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": "get_weather",
            "gen_ai.tool.type": "function",
            "gen_ai.tool.call.id": "call_abc123",
        },
    },
    "invoke_workflow": {
        "name": "invoke_workflow customer_support_pipeline",
        "kind": "internal",
        "attributes": {
            "gen_ai.operation.name": "invoke_workflow",
            "gen_ai.workflow.name": "customer_support_pipeline",
        },
    },
    "plan_with_agent": {
        "name": "plan research_agent",
        "kind": "internal",
        "attributes": {
            "gen_ai.operation.name": "plan",
            "gen_ai.agent.name": "research_agent",
        },
    },
    "plan_without_agent": {
        "name": "plan",
        "kind": "internal",
        "attributes": {
            "gen_ai.operation.name": "plan",
        },
    },
}


# ---------------------------------------------------------------------------
# Invalid golden spans (each violates at least one requirement)
# ---------------------------------------------------------------------------

INVALID_SPANS: dict[str, SpanDescriptor] = {
    "chat_missing_provider": {
        "name": "chat gpt-4",
        "kind": "client",
        "attributes": {
            # gen_ai.provider.name is required and absent.
            "gen_ai.operation.name": "chat",
            "gen_ai.request.model": "gpt-4",
        },
    },
    "chat_bad_token_type": {
        "name": "chat gpt-4",
        "kind": "client",
        "attributes": {
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "openai",
            # usage tokens must be int, not string.
            "gen_ai.usage.input_tokens": "forty-two",
        },
    },
    "chat_unknown_provider": {
        "name": "chat gpt-4",
        "kind": "client",
        "attributes": {
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "totally-made-up",
        },
    },
    "missing_operation_name": {
        "name": "chat gpt-4",
        "kind": "client",
        "attributes": {
            "gen_ai.provider.name": "openai",
        },
    },
    "unknown_operation_name": {
        "name": "frobnicate gpt-4",
        "kind": "client",
        "attributes": {
            "gen_ai.operation.name": "frobnicate",
            "gen_ai.provider.name": "openai",
        },
    },
    "invoke_agent_client_missing_provider": {
        "name": "invoke_agent research_agent",
        "kind": "client",
        "attributes": {
            # provider.name required for CLIENT invoke_agent.
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": "research_agent",
        },
    },
    "execute_tool_missing_tool_name": {
        "name": "execute_tool get_weather",
        "kind": "internal",
        "attributes": {
            "gen_ai.operation.name": "execute_tool",
        },
    },
    "execute_tool_wrong_kind": {
        "name": "execute_tool get_weather",
        "kind": "client",  # execute_tool spans MUST be INTERNAL.
        "attributes": {
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": "get_weather",
        },
    },
    "invoke_workflow_bad_workflow_name_type": {
        "name": "invoke_workflow pipeline",
        "kind": "internal",
        "attributes": {
            "gen_ai.operation.name": "invoke_workflow",
            # workflow.name must be a string.
            "gen_ai.workflow.name": 123,
        },
    },
    "plan_wrong_kind": {
        "name": "plan research_agent",
        "kind": "client",  # plan spans MUST be INTERNAL.
        "attributes": {
            "gen_ai.operation.name": "plan",
            "gen_ai.agent.name": "research_agent",
        },
    },
    "plan_bad_agent_name_type": {
        "name": "plan research_agent",
        "kind": "internal",
        "attributes": {
            "gen_ai.operation.name": "plan",
            # agent.name must be a string.
            "gen_ai.agent.name": 99,
        },
    },
}


# ---------------------------------------------------------------------------
# A full multi-agent trajectory (workflow -> invoke_agent -> plan -> chat ->
# execute_tool). Every span is individually compliant.
# ---------------------------------------------------------------------------

AGENT_TRAJECTORY: list[SpanDescriptor] = [
    {
        "name": "invoke_workflow research_pipeline",
        "kind": "internal",
        "attributes": {
            "gen_ai.operation.name": "invoke_workflow",
            "gen_ai.workflow.name": "research_pipeline",
        },
    },
    {
        "name": "invoke_agent research_agent",
        "kind": "internal",
        "attributes": {
            "gen_ai.operation.name": "invoke_agent",
            "gen_ai.agent.name": "research_agent",
            "gen_ai.request.model": "gpt-4",
        },
    },
    {
        "name": "plan research_agent",
        "kind": "internal",
        "attributes": {
            "gen_ai.operation.name": "plan",
            "gen_ai.agent.name": "research_agent",
        },
    },
    {
        "name": "chat gpt-4",
        "kind": "client",
        "attributes": {
            "gen_ai.operation.name": "chat",
            "gen_ai.provider.name": "openai",
            "gen_ai.request.model": "gpt-4",
            "gen_ai.usage.input_tokens": 320,
            "gen_ai.usage.output_tokens": 210,
            "gen_ai.response.finish_reasons": ["tool_calls"],
        },
    },
    {
        "name": "execute_tool web_search",
        "kind": "internal",
        "attributes": {
            "gen_ai.operation.name": "execute_tool",
            "gen_ai.tool.name": "web_search",
            "gen_ai.tool.type": "function",
        },
    },
]
