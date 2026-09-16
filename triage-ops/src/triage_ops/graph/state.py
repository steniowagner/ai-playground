from typing import Annotated

from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from triage_ops.domain.investigation.schema import (
    InvestigationFailure,
    InvestigationResult,
)
from triage_ops.graph.nodes.prepare_approvals.schema import (
    PendingApproval,
)
from triage_ops.graph.nodes.request_approvals.schema import (
    ApprovalDecision,
)


class State(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages]
    final_result: InvestigationResult | InvestigationFailure | None = None
    pending_approvals: list[PendingApproval] = Field(default_factory=list)
    approval_decisions: list[ApprovalDecision] = Field(default_factory=list)
    is_incident_id_input_invalid: bool = True
    authorized_incident_id: str | None = None
    pending_incident_id_confirmation: str | None = None
