from typing import Annotated

from incident_triage_assistant_langchain.domain.investigation.schema import (
    InvestigationFailure,
    InvestigationResult,
)
from incident_triage_assistant_langchain.graph.nodes.prepare_approvals.schema import (
    PendingApproval,
)
from incident_triage_assistant_langchain.graph.nodes.request_approvals.schema import (
    ApprovalDecision,
)
from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class State(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages]
    final_result: InvestigationResult | InvestigationFailure | None = None
    pending_approvals: list[PendingApproval] = Field(default_factory=list)
    approval_decisions: list[ApprovalDecision] = Field(default_factory=list)
    authorized_incident_ids: set[str] = Field(default_factory=set)
    incident_id_input_invalid: bool = False
