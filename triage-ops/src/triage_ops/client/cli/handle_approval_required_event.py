import json

from triage_ops.graph.event_stream import (
    ApprovalRequiredEvent,
    BaseProposalEvent,
    ExecutingProposalEvent,
    ProposalExecutionFinishedEvent,
    ProposalRejectedEvent,
)
from triage_ops.graph.nodes.request_approvals import (
    ApprovalDecision,
    InvalidApprovalResponse,
)

from .schema import HandleApprovalRequiredEventArgs


def ask_for_approval(
    event: ApprovalRequiredEvent,
) -> list[ApprovalDecision] | None:
    actions = event.actions or []
    decisions: list[ApprovalDecision] = []

    print("\n\n[Approval Required]\n")
    print("The investigation proposed the following actions:")

    for index, action in enumerate(actions, start=1):
        print(f"\n[Action {index}]\n")
        print(f"Kind: {action['kind']}")
        print(f"Proposal-id: {action['proposal_id']}")
        print(f"Incident: {action['incident_id']}")
        print(f"Reason: {action['rationale']}")
        print("Arguments:")
        print(
            json.dumps(
                action["args"],
                indent=2,
                sort_keys=True,
            )
        )

        while True:
            try:
                answer = input("\nApprove this action? [y/n] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return None

            if answer in ("y", "yes"):
                approved = True
                break

            if answer in ("n", "no"):
                approved = False
                break

            print("\nPlease enter 'y' or 'n'.\n")

        decisions.append(
            ApprovalDecision(proposal_id=action["proposal_id"], approved=approved)
        )

    return decisions


def get_entry_message(event: BaseProposalEvent) -> str:
    if isinstance(event, ExecutingProposalEvent):
        return "Executing Proposal"
    if isinstance(event, ProposalRejectedEvent):
        return "Proposal Rejected"
    return "Proposal Execution Finished"


def handle_proposal_execution_event(
    event: BaseProposalEvent,
) -> None:
    if not isinstance(
        event,
        (ProposalExecutionFinishedEvent, ProposalRejectedEvent, ExecutingProposalEvent),
    ):
        return

    print(f"\n[{get_entry_message(event)}]\n")
    print(f"Kind: {event.kind}")
    print(f"Proposal-id: {event.proposal_id}")
    print(f"Incident: {event.incident_id}")
    print("Arguments:")
    print(
        json.dumps(
            event.arguments,
            indent=2,
            sort_keys=True,
        )
    )
    if event.result is not None:
        print(f"Finished Successfully? {'Yes' if event.result['ok'] else 'No'}")
        print("Result:")
        print(
            json.dumps(
                event.result,
                indent=2,
                sort_keys=True,
            )
        )


async def handle_approval_required_event(args: HandleApprovalRequiredEventArgs) -> None:
    approvals_decisions = ask_for_approval(args.event)
    if approvals_decisions is None:
        return

    try:
        async for event in args.graph_runner.resume(
            args.thread_id, approvals_decisions
        ):
            if isinstance(event, BaseProposalEvent):
                handle_proposal_execution_event(event)
    except InvalidApprovalResponse:
        print("\n[Invalid Approval Response]\n\nThe approval response was invalid.")
