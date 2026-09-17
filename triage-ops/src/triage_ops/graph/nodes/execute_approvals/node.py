from langgraph.config import get_stream_writer
from pydantic import ValidationError

from triage_ops.domain.investigation import (
    ExecutableProposal,
)
from triage_ops.graph import State
from triage_ops.graph.event_stream import CustomStreamEvents
from triage_ops.graph.nodes.prepare_approvals import (
    PendingApproval,
)
from triage_ops.services import (
    Service,
    ServiceErrorResponse,
    ServiceErrorResponseDetail,
    ServiceExecutionException,
    ServiceRegistry,
    ServiceResponse,
    ServiceSuccessResponse,
)


def execute_proposal(
    proposal: ExecutableProposal, service_registry: ServiceRegistry
) -> ServiceResponse:
    service: Service = service_registry.get(proposal.kind)

    if not service:
        return ServiceErrorResponse(
            ok=False,
            error=ServiceErrorResponseDetail(
                code="UNKNOWN_TOOL",
                input=proposal.args.model_dump(mode="json"),
                message="Unknown service.",
            ),
        )

    try:
        args = proposal.args.model_validate(proposal.args)
        proposal_response = service.execute(args)
    except ValidationError:
        return ServiceErrorResponse(
            ok=False,
            error=ServiceErrorResponseDetail(
                code="INVALID_ARGUMENT",
                input=proposal.args.model_dump(mode="json"),
                message="Invalid argument.",
            ),
        )
    except ServiceExecutionException:
        return ServiceErrorResponse(
            ok=False,
            error=ServiceErrorResponseDetail(
                code="EXECUTION_ERROR",
                input=proposal.args.model_dump(mode="json"),
                message="Something went wrong.",
            ),
        )

    return proposal_response


def update_approvals_status_from_approved_to_executing(
    approval_decisions: list[PendingApproval],
) -> list[PendingApproval]:
    executing_approvals: list[PendingApproval] = []
    for approved_decision in approval_decisions:
        if approved_decision.status != "approved":
            executing_approvals.append(approved_decision)
            continue

        executing_approvals.append(
            approved_decision.model_copy(update={"status": "executing"})
        )

    return executing_approvals


def execute_approvals_node(state: State, *, service_registry: ServiceRegistry) -> dict:
    executing_proposals = update_approvals_status_from_approved_to_executing(
        state.pending_approvals
    )

    try:
        write_stream_event = get_stream_writer()
    except RuntimeError:
        write_stream_event = None

    executed_proposals: list[PendingApproval] = []
    for executing_proposal in executing_proposals:
        if executing_proposal.status != "executing":
            executed_proposals.append(executing_proposal)
            continue

        if write_stream_event is not None:
            write_stream_event(
                {
                    "event": CustomStreamEvents.EXECUTING_PROPOSAL,
                    "kind": executing_proposal.proposal.kind,
                    "args": executing_proposal.proposal.args.model_dump(mode="json"),
                    "incident_id": executing_proposal.incident_id,
                    "proposal_id": executing_proposal.proposal_id,
                }
            )

        proposal_result = execute_proposal(
            executing_proposal.proposal, service_registry
        )

        executed_proposals.append(
            PendingApproval.model_validate(
                {
                    **executing_proposal.model_dump(),
                    "status": (
                        "executed"
                        if isinstance(proposal_result, ServiceSuccessResponse)
                        else "failed"
                    ),
                    "execution_result": proposal_result,
                }
            )
        )

    return {"pending_approvals": executed_proposals}
