from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ApprovalDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: UUID
    approved: bool


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decisions: list[ApprovalDecision]
