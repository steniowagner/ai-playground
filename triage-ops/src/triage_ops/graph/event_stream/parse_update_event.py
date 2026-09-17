from typing import Any

from pydantic import ValidationError

from triage_ops.graph.nodes.prepare_approvals import PendingApproval

from .schema import (
    ApprovalRequiredEvent,
    Event,
    ExecutingProposalEvent,
    GraphEvent,
    InvestigationCompletedEvent,
    ProposalExecutionFinishedEvent,
)


def parse_update_event(payload: Any, base_event: Event) -> list[GraphEvent]:
    events: list[GraphEvent] = []

    if not isinstance(payload, dict):
        return events

    interrupts = payload.get("__interrupt__", ())
    if not isinstance(interrupts, (list, tuple)):
        interrupts = ()

    for interruption in interrupts:
        value = getattr(interruption, "value", None)
        actions = value.get("actions") if isinstance(value, dict) else None
        if not isinstance(actions, list):
            continue

        try:
            events.append(
                ApprovalRequiredEvent(
                    **base_event.model_dump(),
                    actions=actions,
                )
            )
        except ValidationError:
            continue

    for node_update in payload.values():
        if not isinstance(node_update, dict):
            continue

        final_result = node_update.get("final_result")
        if final_result is not None:
            try:
                events.append(
                    InvestigationCompletedEvent(
                        **base_event.model_dump(),
                        result=final_result,
                    )
                )
            except ValidationError:
                pass

        pending_approvals = node_update.get("pending_approvals")
        if not isinstance(pending_approvals, (list, tuple)):
            continue

        for pending_approval in pending_approvals:
            if not isinstance(pending_approval, PendingApproval):
                continue

            if pending_approval.status == "executing":
                events.append(
                    ExecutingProposalEvent(
                        **base_event.model_dump(),
                        kind=pending_approval.proposal.kind,
                        arguments=pending_approval.proposal.args.model_dump(
                            mode="json"
                        ),
                        incident_id=pending_approval.incident_id,
                        proposal_id=pending_approval.proposal_id,
                    )
                )

            if pending_approval.status in {"executed", "failed", "rejected"}:
                execution_result = pending_approval.execution_result
                events.append(
                    ProposalExecutionFinishedEvent(
                        **base_event.model_dump(),
                        kind=pending_approval.proposal.kind,
                        arguments=pending_approval.proposal.args.model_dump(
                            mode="json"
                        ),
                        incident_id=pending_approval.incident_id,
                        proposal_id=pending_approval.proposal_id,
                        result=(
                            execution_result.model_dump(mode="json")
                            if execution_result is not None
                            else None
                        ),
                    )
                )

    return events
