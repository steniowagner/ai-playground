from typing import Annotated

from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from incident_triage_assistant_langchain.investigation.schema import (
    InvestigationFailure,
    InvestigationResult,
)
from incident_triage_assistant_langchain.nodes.prepare_approvals.schema import (
    PendingApproval,
)
from incident_triage_assistant_langchain.nodes.request_approvals.schema import (
    ApprovalDecision,
)


class State(BaseModel):
    messages: Annotated[list[AnyMessage], add_messages]
    final_result: InvestigationResult | InvestigationFailure | None = None
    pending_approvals: list[PendingApproval] = Field(default_factory=list)
    approval_decisions: list[ApprovalDecision] = Field(default_factory=list)
