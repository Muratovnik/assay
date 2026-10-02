"""SDK-visible receipt shapes; history remains the persistence/validation owner."""
from typing import Annotated, Any, Literal

from pydantic import Field, StrictFloat, StrictInt
from typing_extensions import TypedDict

from .history import _CODE

Identifier = Annotated[str, Field(pattern=_CODE.pattern)]
Amount = Annotated[StrictInt, Field(ge=0)] | Annotated[StrictFloat, Field(ge=0)] | None


class ReceiptRoute(TypedDict, total=False):
    __pydantic_config__ = {"extra": "forbid"}
    model: str | None
    effort: Identifier | None
    service_tier: Identifier | None


class ReceiptReference(TypedDict, total=False):
    __pydantic_config__ = {"extra": "forbid"}
    evidence_id: Identifier
    source_id: Identifier
    id: Identifier


References = Identifier | ReceiptReference | Annotated[list[Identifier | ReceiptReference], Field(max_length=256)] | None


class ReceiptOutcome(TypedDict, total=False):
    __pydantic_config__ = {"extra": "forbid"}
    status: Identifier
    basis: Identifier | None
    evidence_refs: References


class ReceiptUsage(TypedDict, total=False):
    __pydantic_config__ = {"extra": "forbid"}
    input_tokens: Amount
    inputTokens: Amount
    cached_input_tokens: Amount
    cache_read_input_tokens: Amount
    cacheReadInputTokens: Amount
    cache_creation_input_tokens: Amount
    cacheCreationInputTokens: Amount
    output_tokens: Amount
    outputTokens: Amount
    reasoning_output_tokens: Amount
    reasoningOutputTokens: Amount
    total_tokens: Amount
    totalTokens: Amount


class ExecutionReceipt(TypedDict, total=False):
    __pydantic_config__ = {"extra": "forbid"}
    status: Literal["launched", "completed", "failed", "interrupted", "unknown"]
    packet_id: Identifier
    execution_ref: Identifier | None
    requested: ReceiptRoute | None
    observed: ReceiptRoute | None
    requested_model: str | None
    requested_effort: Identifier | None
    requested_service_tier: Identifier | None
    observed_model: str | None
    observed_effort: Identifier | None
    observed_service_tier: Identifier | None
    actual_model: str | None
    actual_effort: Identifier | None
    actual_service_tier: Identifier | None
    usage: ReceiptUsage | None
    usage_provenance: Identifier
    outcome: Identifier | ReceiptOutcome
    outcome_basis: Identifier | None
    evidence: References
    evidence_refs: References
    cost_observation: dict[str, Any]
    task_description: str


class OutcomeResult(TypedDict, total=False):
    __pydantic_config__ = {"extra": "forbid"}
    status: str
    decision_id: str
    recorded: bool
    persisted: bool
    history_schema: int
    namespace: str
    record_type: str
    created_at: str
    expires_at: str
    privacy_mode: str
    execution: dict[str, Any]
    packet_id: str
    attempt_key: str
    write_status: Literal["written", "unchanged"]
