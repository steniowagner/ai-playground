from .schema import (
    ApprovalRequiredEvent,
    Event,
    ExecutingProposalEvent,
    GraphEvent,
    InvestigationCompletedEvent,
    ProposalExecutionFinishedEvent,
)


def parse_update_event(payload: dict, base_event: Event) -> list[GraphEvent]:
    events: list[GraphEvent] = []

    interrupts = payload.get("__interrupt__", ())

    for interruption in interrupts:
        events.append(
            ApprovalRequiredEvent(
                **base_event.model_dump(), actions=interruption.value["actions"]
            )
        )

    for node_update in payload.values():
        if not isinstance(node_update, dict):
            continue

        final_result = node_update.get("final_result")
        if final_result is not None:
            events.append(
                InvestigationCompletedEvent(
                    **base_event.model_dump(), result=final_result
                )
            )

        pending_approvals = node_update.get("pending_approvals")
        if pending_approvals is None:
            continue

        for pending_approval in pending_approvals:
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

            if (
                pending_approval.status == "executed"
                or pending_approval.status == "rejected"
            ):
                events.append(
                    ProposalExecutionFinishedEvent(
                        **base_event.model_dump(),
                        kind=pending_approval.proposal.kind,
                        arguments=pending_approval.proposal.args.model_dump(
                            mode="json"
                        ),
                        incident_id=pending_approval.incident_id,
                        proposal_id=pending_approval.proposal_id,
                        result=pending_approval.execution_result.model_dump(
                            mode="json"
                        ),
                    )
                )

    return events
