from collections import Counter

from langgraph.types import interrupt
from pydantic import ValidationError
from triage_ops.graph.nodes.prepare_approvals.schema import (
    PendingApproval,
)
from triage_ops.graph.state import State

from .exceptions import InvalidApprovalResponse
from .schema import ApprovalDecision, ApprovalResponse


def validate_approval_decisions(
    pending_approvals: list[PendingApproval],
    decisions: list[ApprovalDecision],
) -> None:
    expected_ids = {
        approval.proposal_id
        for approval in pending_approvals
        if approval.status == "pending"
    }

    received_ids = [decision.proposal_id for decision in decisions]
    id_counts = Counter(received_ids)

    duplicate_ids = {
        proposal_id for proposal_id, count in id_counts.items() if count > 1
    }

    received_id_set = set(received_ids)
    unknown_ids = received_id_set - expected_ids
    missing_ids = expected_ids - received_id_set

    if duplicate_ids:
        raise InvalidApprovalResponse(f"Duplicate approval decisions: {duplicate_ids}")

    if unknown_ids:
        raise InvalidApprovalResponse(f"Unknown approval decisions: {unknown_ids}")

    if missing_ids:
        raise InvalidApprovalResponse(f"Missing approval decisions: {missing_ids}")


def update_pending_approvals_status_based_on_decisions(
    pending_approvals: list[PendingApproval], decisions: list[ApprovalDecision]
):
    validate_approval_decisions(pending_approvals, decisions)

    decisions_by_id = {decision.proposal_id: decision for decision in decisions}

    return [
        approval
        if approval.status != "pending"
        else approval.model_copy(
            update={
                "status": (
                    "approved"
                    if decisions_by_id[approval.proposal_id].approved
                    else "rejected"
                )
            }
        )
        for approval in pending_approvals
    ]


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
    try:
        response = ApprovalResponse.model_validate(resumed_value)
    except ValidationError as exc:
        raise InvalidApprovalResponse(
            "The approval response has an invalid structure."
        ) from exc
    pending_approvals_with_decisions = (
        update_pending_approvals_status_based_on_decisions(
            state.pending_approvals, response.decisions
        )
    )

    return {
        "approval_decisions": response.decisions,
        "pending_approvals": pending_approvals_with_decisions,
    }
