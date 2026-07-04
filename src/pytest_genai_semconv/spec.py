"""Embedded snapshot of the OpenTelemetry GenAI semantic conventions.

The attribute names, value types, enum values, and per-operation span
requirements below are derived directly from the live specification in the
OpenTelemetry GenAI semantic conventions repository:

    Source: open-telemetry/semantic-conventions-genai
    Ref:    43633a68ef8f8ed87a1d5eb205990311ca708bf1 (main)
    Files:  model/gen-ai/registry.yaml   (attribute keys, types, enum values)
            model/gen-ai/spans.yaml      (span types, kinds, requirement levels)

The GenAI conventions were moved out of open-telemetry/semantic-conventions
into the dedicated semantic-conventions-genai repository; the corresponding
attribute definitions in the original repository are now marked deprecated
("Moved"). This module therefore tracks the dedicated repository.

The ``plan`` operation and the ``gen_ai.plan.internal`` span were introduced
by semantic-conventions-genai#97.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Enum value sets (registry.yaml)
# ---------------------------------------------------------------------------

# gen_ai.operation.name well-known values.
OPERATION_NAMES: frozenset[str] = frozenset(
    {
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
)

# gen_ai.output.type well-known values.
OUTPUT_TYPES: frozenset[str] = frozenset({"text", "json", "image", "speech"})

# gen_ai.provider.name well-known values.
PROVIDER_NAMES: frozenset[str] = frozenset(
    {
        "openai",
        "gcp.gen_ai",
        "gcp.vertex_ai",
        "gcp.gemini",
        "anthropic",
        "cohere",
        "azure.ai.inference",
        "azure.ai.openai",
        "ibm.watsonx.ai",
        "aws.bedrock",
        "perplexity",
        "x_ai",
        "deepseek",
        "groq",
        "mistral_ai",
        "moonshot_ai",
    }
)

# gen_ai.token.type well-known values.
TOKEN_TYPES: frozenset[str] = frozenset({"input", "output"})


# ---------------------------------------------------------------------------
# Attribute value types (registry.yaml). Values are the spec's type strings.
# ---------------------------------------------------------------------------

ATTRIBUTE_TYPES: dict[str, str] = {
    "gen_ai.provider.name": "string",  # enum, string-valued
    "gen_ai.request.model": "string",
    "gen_ai.request.max_tokens": "int",
    "gen_ai.request.choice.count": "int",
    "gen_ai.request.temperature": "double",
    "gen_ai.request.top_p": "double",
    "gen_ai.request.top_k": "int",
    "gen_ai.request.stop_sequences": "string[]",
    "gen_ai.request.frequency_penalty": "double",
    "gen_ai.request.presence_penalty": "double",
    "gen_ai.request.encoding_formats": "string[]",
    "gen_ai.request.seed": "int",
    "gen_ai.request.stream": "boolean",
    "gen_ai.request.reasoning.level": "string",
    "gen_ai.response.id": "string",
    "gen_ai.response.model": "string",
    "gen_ai.response.finish_reasons": "string[]",
    "gen_ai.response.time_to_first_chunk": "double",
    "gen_ai.usage.input_tokens": "int",
    "gen_ai.usage.cache_read.input_tokens": "int",
    "gen_ai.usage.cache_creation.input_tokens": "int",
    "gen_ai.usage.output_tokens": "int",
    "gen_ai.usage.reasoning.output_tokens": "int",
    "gen_ai.token.type": "string",  # enum, string-valued
    "gen_ai.conversation.id": "string",
    "gen_ai.conversation.compacted": "boolean",
    "gen_ai.agent.id": "string",
    "gen_ai.agent.name": "string",
    "gen_ai.agent.description": "string",
    "gen_ai.agent.version": "string",
    "gen_ai.tool.name": "string",
    "gen_ai.tool.call.id": "string",
    "gen_ai.tool.description": "string",
    "gen_ai.tool.type": "string",
    "gen_ai.tool.call.arguments": "any",
    "gen_ai.tool.call.result": "any",
    "gen_ai.tool.definitions": "any",
    "gen_ai.data_source.id": "string",
    "gen_ai.operation.name": "string",  # enum, string-valued
    "gen_ai.output.type": "string",  # enum, string-valued
    "gen_ai.embeddings.dimension.count": "int",
    "gen_ai.retrieval.documents": "any",
    "gen_ai.retrieval.query.text": "string",
    "gen_ai.retrieval.top_k": "int",
    "gen_ai.memory.store.id": "string",
    "gen_ai.memory.record.id": "string",
    "gen_ai.memory.record.count": "int",
    "gen_ai.memory.query.text": "string",
    "gen_ai.memory.records": "any",
    "gen_ai.system_instructions": "any",
    "gen_ai.input.messages": "any",
    "gen_ai.output.messages": "any",
    "gen_ai.evaluation.name": "string",
    "gen_ai.evaluation.score.value": "double",
    "gen_ai.evaluation.score.label": "string",
    "gen_ai.evaluation.explanation": "string",
    "gen_ai.prompt.name": "string",
    "gen_ai.prompt.version": "string",
    "gen_ai.workflow.name": "string",
}

# Enumerated string attributes and their allowed value sets.
ENUM_ATTRIBUTES: dict[str, frozenset[str]] = {
    "gen_ai.operation.name": OPERATION_NAMES,
    "gen_ai.output.type": OUTPUT_TYPES,
    "gen_ai.provider.name": PROVIDER_NAMES,
    "gen_ai.token.type": TOKEN_TYPES,
}


# ---------------------------------------------------------------------------
# Per-operation span profiles (spans.yaml)
# ---------------------------------------------------------------------------

# Span kinds are expressed as the SDK's uppercase names.
SPAN_KIND_CLIENT = "CLIENT"
SPAN_KIND_INTERNAL = "INTERNAL"


@dataclass(frozen=True)
class SpanProfile:
    """Requirements for a specific gen_ai span type.

    Attributes:
        operation_name: The value ``gen_ai.operation.name`` must carry.
        span_type: The convention span type identifier (e.g.
            ``gen_ai.plan.internal``).
        required_attributes: Attribute keys that MUST be present.
        allowed_kinds: Span kinds permitted for this operation. Empty means
            any kind is accepted.
        span_name_prefix: When set, the span name SHOULD begin with this token
            (typically the operation name).
    """

    operation_name: str
    span_type: str
    required_attributes: tuple[str, ...]
    allowed_kinds: tuple[str, ...] = field(default_factory=tuple)
    span_name_prefix: str | None = None


# Requirement levels below reflect ``requirement_level: required`` entries in
# model/gen-ai/spans.yaml for each span type. Conditionally-required and
# recommended attributes are intentionally not enforced as hard requirements.
_PROFILES: dict[str, SpanProfile] = {
    # gen_ai.inference.client — chat / text_completion / generate_content.
    # required: gen_ai.operation.name, gen_ai.provider.name.
    "chat": SpanProfile(
        operation_name="chat",
        span_type="gen_ai.inference.client",
        required_attributes=("gen_ai.operation.name", "gen_ai.provider.name"),
        allowed_kinds=(SPAN_KIND_CLIENT, SPAN_KIND_INTERNAL),
        span_name_prefix="chat",
    ),
    "text_completion": SpanProfile(
        operation_name="text_completion",
        span_type="gen_ai.inference.client",
        required_attributes=("gen_ai.operation.name", "gen_ai.provider.name"),
        allowed_kinds=(SPAN_KIND_CLIENT, SPAN_KIND_INTERNAL),
        span_name_prefix="text_completion",
    ),
    "generate_content": SpanProfile(
        operation_name="generate_content",
        span_type="gen_ai.inference.client",
        required_attributes=("gen_ai.operation.name", "gen_ai.provider.name"),
        allowed_kinds=(SPAN_KIND_CLIENT, SPAN_KIND_INTERNAL),
        span_name_prefix="generate_content",
    ),
    # gen_ai.embeddings.client.
    "embeddings": SpanProfile(
        operation_name="embeddings",
        span_type="gen_ai.embeddings.client",
        required_attributes=("gen_ai.operation.name", "gen_ai.provider.name"),
        allowed_kinds=(SPAN_KIND_CLIENT, SPAN_KIND_INTERNAL),
        span_name_prefix="embeddings",
    ),
    # gen_ai.create_agent.client.
    "create_agent": SpanProfile(
        operation_name="create_agent",
        span_type="gen_ai.create_agent.client",
        required_attributes=("gen_ai.operation.name", "gen_ai.provider.name"),
        allowed_kinds=(SPAN_KIND_CLIENT, SPAN_KIND_INTERNAL),
        span_name_prefix="create_agent",
    ),
    # gen_ai.execute_tool.internal — span kind MUST be INTERNAL per spans.yaml.
    # required: gen_ai.operation.name, gen_ai.tool.name.
    "execute_tool": SpanProfile(
        operation_name="execute_tool",
        span_type="gen_ai.execute_tool.internal",
        required_attributes=("gen_ai.operation.name", "gen_ai.tool.name"),
        allowed_kinds=(SPAN_KIND_INTERNAL,),
        span_name_prefix="execute_tool",
    ),
    # gen_ai.invoke_workflow.internal.
    "invoke_workflow": SpanProfile(
        operation_name="invoke_workflow",
        span_type="gen_ai.invoke_workflow.internal",
        required_attributes=("gen_ai.operation.name",),
        allowed_kinds=(SPAN_KIND_INTERNAL,),
        span_name_prefix="invoke_workflow",
    ),
    # gen_ai.plan.internal — introduced by semantic-conventions-genai#97.
    # required: gen_ai.operation.name. Span kind MUST be INTERNAL.
    "plan": SpanProfile(
        operation_name="plan",
        span_type="gen_ai.plan.internal",
        required_attributes=("gen_ai.operation.name",),
        allowed_kinds=(SPAN_KIND_INTERNAL,),
        span_name_prefix="plan",
    ),
}


def profile_for_operation(operation_name: str) -> SpanProfile | None:
    """Return the :class:`SpanProfile` for a gen_ai operation, or ``None``.

    ``invoke_agent`` is handled dynamically (see :func:`invoke_agent_profile`)
    because its requirements depend on span kind, so it is not stored here.
    """

    if operation_name == "invoke_agent":
        # A default (internal) profile; callers that know the kind should use
        # invoke_agent_profile for the kind-sensitive requirements.
        return invoke_agent_profile(SPAN_KIND_INTERNAL)
    return _PROFILES.get(operation_name)


def invoke_agent_profile(span_kind: str) -> SpanProfile:
    """Return the invoke_agent profile appropriate for ``span_kind``.

    Per spans.yaml, ``gen_ai.invoke_agent.client`` additionally requires
    ``gen_ai.provider.name``, whereas ``gen_ai.invoke_agent.internal`` does
    not.
    """

    if span_kind == SPAN_KIND_CLIENT:
        return SpanProfile(
            operation_name="invoke_agent",
            span_type="gen_ai.invoke_agent.client",
            required_attributes=(
                "gen_ai.operation.name",
                "gen_ai.provider.name",
            ),
            allowed_kinds=(SPAN_KIND_CLIENT,),
            span_name_prefix="invoke_agent",
        )
    return SpanProfile(
        operation_name="invoke_agent",
        span_type="gen_ai.invoke_agent.internal",
        required_attributes=("gen_ai.operation.name",),
        allowed_kinds=(SPAN_KIND_INTERNAL,),
        span_name_prefix="invoke_agent",
    )
