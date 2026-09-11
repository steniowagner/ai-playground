from typing import Literal
from uuid import UUID

from incident_triage_assistant_langchain.investigation.schema import ExecutableProposal
from incident_triage_assistant_langchain.services.schema import ServiceResponse
from pydantic import BaseModel, ConfigDict

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
