from triage_ops.graph.event_stream import (
    ApprovalRequiredEvent,
    BaseToolEvent,
    InvestigationCompletedEvent,
    MessageChunkEvent,
    ModelThinkingEvent,
)
from triage_ops.graph.runner import GraphRunner

from .handle_approval_required_event import handle_approval_required_event
from .handle_investigation_completed_event import handle_investigation_completed_event
from .handle_message_event import handle_message_event
from .handle_tool_event import handle_tool_event
from .print_header import print_header
from .schema import HandleApprovalRequiredEventArgs


async def run_cli(graph_runner: GraphRunner, thread_id: str) -> None:
    print_header()

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            return

        if not user_input:
            continue

        if user_input.lower() == "exit":
            return

        events = graph_runner.start(thread_id, user_input)

        messages_event_utils = {"previous_message_event": None}

        async for event in events:
            if isinstance(event, (MessageChunkEvent, ModelThinkingEvent)):
                handle_message_event(event, messages_event_utils)

            if isinstance(event, BaseToolEvent):
                handle_tool_event(event)

            if isinstance(event, ApprovalRequiredEvent):
                await handle_approval_required_event(
                    HandleApprovalRequiredEventArgs(
                        graph_runner=graph_runner,
                        thread_id=thread_id,
                        event=event,
                    )
                )

            if isinstance(event, InvestigationCompletedEvent):
                handle_investigation_completed_event(event)

        print("\n")
