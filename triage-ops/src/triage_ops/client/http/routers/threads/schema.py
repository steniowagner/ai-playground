from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from triage_ops.graph.nodes.request_approvals import (
    ApprovalDecision,
)


class CreateThreadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    thread_id: UUID


class StartStreamRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    message: str = Field(min_length=1)


class ResumeStreamRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decisions: list[ApprovalDecision]
