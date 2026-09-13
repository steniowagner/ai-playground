from incident_triage_assistant_langchain.domain.investigation.schema import (
    ExecutableProposal,
)
from incident_triage_assistant_langchain.graph.nodes.prepare_approvals.schema import (
    PendingApproval,
)
from incident_triage_assistant_langchain.graph.state import State
from incident_triage_assistant_langchain.services.bootstrap_services import (
    ServiceRegistry,
)
from incident_triage_assistant_langchain.services.exceptions import (
    ServiceExecutionException,
)
from incident_triage_assistant_langchain.services.schema import (
    ServiceErrorResponse,
    ServiceErrorResponseDetail,
    ServiceResponse,
    ServiceSuccessResponse,
)
from incident_triage_assistant_langchain.services.service import (
    Service,
)
from pydantic import ValidationError


def execute_proposal(
    proposal: ExecutableProposal, service_registry: ServiceRegistry
) -> ServiceResponse:
    service: Service = service_registry.get(proposal.kind)

    if not service:
        return ServiceErrorResponse(
            ok=False,
            data=ServiceErrorResponseDetail(
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
            data=ServiceErrorResponseDetail(
                code="INVALID_ARGUMENT",
                input=proposal.args.model_dump(mode="json"),
                message="Invalid argument.",
            ),
        )
    except ServiceExecutionException:
        return ServiceErrorResponse(
            ok=False,
            data=ServiceErrorResponseDetail(
                code="EXECUTION_ERROR",
                input=proposal.args.model_dump(mode="json"),
                message="Something went wrong.",
            ),
        )

    return proposal_response


def update_approvals_status_from_approved_to_executing(
    approved_decisions: list[PendingApproval],
) -> list[PendingApproval]:
    executing_approvals: list[PendingApproval] = []
    for approved_decision in approved_decisions:
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

    executed_proposals: list[PendingApproval] = []
    for executing_proposal in executing_proposals:
        if executing_proposal.status != "executing":
            executed_proposals.append(executing_proposal)
            continue

        proposal_result = execute_proposal(
            executing_proposal.proposal, service_registry
        )

        executed_proposals.append(
            executing_proposal.model_copy(
                update={
                    "status": "executed"
                    if isinstance(proposal_result, ServiceSuccessResponse)
                    else "failed",
                    "execution_result": proposal_result,
                }
            )
        )

    return {"pending_approvals": executed_proposals}
