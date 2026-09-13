from abc import ABC, abstractmethod
from typing import Annotated, Any, Literal, TypeAlias
from uuid import UUID

from incident_triage_assistant_langchain.investigation.schema import InvestigationResult
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


class InvestigationCompletedEvent(Event):
    type: Literal["investigation_completed"] = "investigation_completed"
    result: InvestigationResult


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
    | ToolStartedEvent
    | ToolFinishedEvent
    | ApprovalRequiredEvent
    | InvestigationCompletedEvent
    | ModelThinkingEvent,
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
