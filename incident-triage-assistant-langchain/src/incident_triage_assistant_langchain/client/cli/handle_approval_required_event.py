import json

from incident_triage_assistant_langchain.graph.event_stream.schema import (
    ApprovalRequiredEvent,
    BaseProposalEvent,
    ExecutingProposalEvent,
    ProposalExecutionFinishedEvent,
)
from incident_triage_assistant_langchain.graph.nodes.request_approvals.schema import (
    ApprovalDecision,
)

from .schema import HandleApprovalRequiredEventArgs


def ask_for_approval(
    event: ApprovalRequiredEvent,
) -> list[ApprovalDecision]:
    actions = event.actions or []
    decisions: list[ApprovalDecision] = []

    print("\n\n[Approval Required]\n")
    print("The investigation proposed the following actions:\n")

    for index, action in enumerate(actions, start=1):
        print(f"[Action {index}]\n")
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
                return

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


def handle_proposal_execution_event(
    event: BaseProposalEvent,
) -> None:
    if not isinstance(event, (ProposalExecutionFinishedEvent, ExecutingProposalEvent)):
        return

    entry_message = (
        "Executing Proposal"
        if isinstance(event, ExecutingProposalEvent)
        else "Proposal Execution Finished"
    )
    print(f"[{entry_message}]\n")

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
    approval_events = args.graph_runner.resume(args.thread_id, approvals_decisions)
    async for approval_event in approval_events:
        if isinstance(approval_event, BaseProposalEvent):
            handle_proposal_execution_event(approval_event)
