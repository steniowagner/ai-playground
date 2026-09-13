from incident_triage_assistant_langchain.graph.nodes.prepare_approvals.schema import (
    PendingApproval,
)
from incident_triage_assistant_langchain.graph.state import State
from langgraph.types import interrupt

from .schema import ApprovalDecision, ApprovalResponse


def update_pending_approvals_status_based_on_decisions(
    pending_approvals: list[PendingApproval], decisions: list[ApprovalDecision]
):
    decisions_by_id = {decision.proposal_id: decision for decision in decisions}

    pending_approvals_with_decisions = []
    for pending_approval in pending_approvals:
        decision = decisions_by_id.get(pending_approval.proposal_id)

        if pending_approval.status != "pending" or decision is None:
            pending_approvals_with_decisions.append(pending_approval)
            continue

        pending_approvals_with_decisions.append(
            pending_approval.model_copy(
                update={"status": ("approved" if decision.approved else "rejected")}
            )
        )

    return pending_approvals_with_decisions


def request_approvals_node(state: State) -> dict:
    approval_request = {
        "type": "action_approval_request",
        "actions": [
            {
                "proposal_id": str(record.proposal_id),
                "incident_id": record.incident_id,
                "kind": record.proposal.kind,
                "rationale": record.proposal.rationale,
                "args": record.proposal.args.model_dump(mode="json"),
            }
            for record in state.pending_approvals
            if record.status == "pending"
        ],
    }

    resumed_value = interrupt(approval_request)
    response = ApprovalResponse.model_validate(resumed_value)
    pending_approvals_with_decisions = (
        update_pending_approvals_status_based_on_decisions(
            state.pending_approvals, response.decisions
        )
    )

    return {
        "approval_decisions": response.decisions,
        "pending_approvals": pending_approvals_with_decisions,
    }
