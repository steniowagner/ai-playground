from uuid import UUID

from pydantic import BaseModel, ConfigDict, StrictBool


class ApprovalDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: UUID
    approved: StrictBool


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decisions: list[ApprovalDecision]
