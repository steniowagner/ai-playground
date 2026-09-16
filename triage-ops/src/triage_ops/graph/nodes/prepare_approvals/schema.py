from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from triage_ops.domain.investigation.schema import (
    ExecutableProposal,
)
from triage_ops.services.schema import ServiceResponse

ApprovalStatus = Literal[
    "pending",
    "approved",
    "rejected",
    "executing",
    "executed",
    "failed",
]


class PendingApproval(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    proposal_id: UUID
    incident_id: str
    proposal: ExecutableProposal
    status: ApprovalStatus
    execution_result: ServiceResponse | None = None
