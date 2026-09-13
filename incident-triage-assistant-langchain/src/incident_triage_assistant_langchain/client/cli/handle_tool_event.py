from incident_triage_assistant_langchain.graph.event_stream.schema import (
    BaseToolEvent,
    ToolFailedEvent,
    ToolFinishedEvent,
    ToolSkippedEvent,
    ToolStartedEvent,
)


def handle_tool_event(event: BaseToolEvent) -> None:
    print("\n[Tool Calling]\n")
    print(f"Tool: {event.tool}")

    if isinstance(event, ToolStartedEvent):
        print("Status: Starting")

    if isinstance(event, ToolFinishedEvent):
        print("Status: Finished")
        print(f"Finished Successfully?: {'Yes' if event.ok else 'No'}")

    if isinstance(event, ToolFailedEvent):
        print("Status: Error")
        print(f"Error Code: {event.error_code}")

    if isinstance(event, ToolSkippedEvent):
        print("Status: Skipped")
        print(f"Reason: {event.reason}")

    print(f"Arguments: {event.model_dump_json(indent=2)}")
