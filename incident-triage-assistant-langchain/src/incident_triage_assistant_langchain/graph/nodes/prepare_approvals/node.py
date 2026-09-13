from uuid import uuid4

from incident_triage_assistant_langchain.domain.investigation.schema import (
    ExecutableProposal,
    InvestigationResult,
)
from incident_triage_assistant_langchain.graph.state import State

from .schema import PendingApproval


def prepare_approvals_node(state: State) -> dict:
    investigation_result = state.final_result

    if not isinstance(investigation_result, InvestigationResult):
        return {"pending_approvals": []}

    pending_approvals = [
        PendingApproval(
            proposal_id=uuid4(),
            proposal=recommended_action,
            incident_id=state.final_result.incident_id,
            status="pending",
        )
        for recommended_action in investigation_result.recommended_actions
        if isinstance(recommended_action, ExecutableProposal)
    ]

    return {"pending_approvals": pending_approvals}
