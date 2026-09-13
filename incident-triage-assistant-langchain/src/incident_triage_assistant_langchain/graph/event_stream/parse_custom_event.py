from incident_triage_assistant_langchain.graph.stream.schema import StreamEvents

from .schema import (
    Event,
    GraphEvent,
    ToolFailedEvent,
    ToolFinishedEvent,
    ToolSkippedEvent,
    ToolStartedEvent,
)


def parse_custom_event(payload: dict, base_event: Event) -> GraphEvent | None:
    match payload["event"]:
        case StreamEvents.TOOL_STARTED:
            return ToolStartedEvent(
                **base_event.model_dump(),
                arguments=payload.get("args"),
                tool=payload.get("tool"),
            )

        case StreamEvents.TOOL_FINISHED:
            return ToolFinishedEvent(
                **base_event.model_dump(),
                arguments=payload.get("args"),
                tool=payload.get("tool"),
                ok=payload.get("ok"),
            )

        case StreamEvents.TOOL_FAILED:
            return ToolFailedEvent(
                **base_event.model_dump(),
                arguments=payload.get("args"),
                tool=payload.get("tool"),
                error_code=payload.get("code"),
            )

        case StreamEvents.TOOL_SKIPPED:
            return ToolSkippedEvent(
                **base_event.model_dump(),
                arguments=payload.get("args"),
                tool=payload.get("tool"),
                reason=payload.get("code"),
            )

        case _:
            return None
