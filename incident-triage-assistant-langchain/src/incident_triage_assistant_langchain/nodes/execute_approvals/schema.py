from incident_triage_assistant_langchain.nodes.prepare_approvals.schema import (
    ApprovalStatus,
    PendingApproval,
)
from pydantic import BaseModel, ConfigDict


class UpdateApprovedProposalsStatusArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    from_state: ApprovalStatus
    to_state: ApprovalStatus
    approvals: list[PendingApproval]
