from abc import ABC, abstractmethod
from enum import Enum
from typing import Annotated, Any, Literal, TypeAlias
from uuid import UUID

from incident_triage_assistant_langchain.domain.investigation.schema import (
    InvestigationOutcome,
)
from langgraph.types import Command
from pydantic import BaseModel, ConfigDict, Field

GraphInput: TypeAlias = dict[str, Any] | Command


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: UUID
    thread_id: str


class MessageChunkEvent(Event):
    type: Literal["message_chunk"] = "message_chunk"
    content: str


class ModelThinkingEvent(Event):
    type: Literal["model_thinking"] = "model_thinking"
    content: str


class BaseToolEvent:
    arguments: dict
    tool: str


class ToolStartedEvent(Event, BaseToolEvent):
    type: Literal["tool_started"] = "tool_started"


class ToolFinishedEvent(Event, BaseToolEvent):
    type: Literal["tool_finished"] = "tool_finished"
    ok: bool


class ToolFailedEvent(Event, BaseToolEvent):
    type: Literal["tool_failed"] = "tool_failed"
    error_code: str | None = None


class ToolSkippedEvent(Event, BaseToolEvent):
    type: Literal["tool_skipped"] = "tool_skipped"
    reason: str


class ApprovalRequiredEvent(Event):
    type: Literal["approval_required"] = "approval_required"
    actions: list[dict]


class InvalidApprovalResponseEvent(Event):
    type: Literal["invalid_approval_response"] = "invalid_approval_response"
    code: Literal["INVALID_APPROVAL_RESPONSE"] = "INVALID_APPROVAL_RESPONSE"
    message: str


class InvestigationCompletedEvent(Event):
    type: Literal["investigation_completed"] = "investigation_completed"
    result: InvestigationOutcome


class BaseProposalEvent(Event):
    kind: str
    arguments: dict
    incident_id: str
    proposal_id: UUID
    result: dict | None = None


class ExecutingProposalEvent(BaseProposalEvent):
    type: Literal["executing_proposal"] = "executing_proposal"


class ProposalExecutionFinishedEvent(BaseProposalEvent):
    type: Literal["proposal_execution_finished"] = "proposal_execution_finished"


GraphEvent = Annotated[
    MessageChunkEvent
    | ToolFailedEvent
    | ToolSkippedEvent
    | ToolStartedEvent
    | ToolFinishedEvent
    | ApprovalRequiredEvent
    | InvalidApprovalResponseEvent
    | InvestigationCompletedEvent
    | ModelThinkingEvent
    | ExecutingProposalEvent
    | ProposalExecutionFinishedEvent,
    Field(discriminator="type"),
]


class GraphEventStream(ABC):
    @abstractmethod
    async def emit(self, event: GraphEvent) -> None:
        raise NotImplementedError


class ParseGraphEventArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mode: str
    payload: Any
    thread_id: str


class CustomStreamEvents(str, Enum):
    TOOL_STARTED = "tool_started"
    TOOL_SKIPPED = "tool_skipped"
    TOOL_FAILED = "tool_failed"
    TOOL_FINISHED = "tool_finished"
