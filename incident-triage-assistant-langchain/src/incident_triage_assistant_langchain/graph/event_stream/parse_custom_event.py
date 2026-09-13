from incident_triage_assistant_langchain.graph.event_stream.schema import (
    CustomStreamEvents,
)

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
        case CustomStreamEvents.TOOL_STARTED:
            return ToolStartedEvent(
                **base_event.model_dump(),
                arguments=payload.get("args"),
                tool=payload.get("tool"),
            )

        case CustomStreamEvents.TOOL_FINISHED:
            return ToolFinishedEvent(
                **base_event.model_dump(),
                arguments=payload.get("args"),
                tool=payload.get("tool"),
                ok=payload.get("ok"),
            )

        case CustomStreamEvents.TOOL_FAILED:
            return ToolFailedEvent(
                **base_event.model_dump(),
                arguments=payload.get("args"),
                tool=payload.get("tool"),
                error_code=payload.get("code"),
            )

        case CustomStreamEvents.TOOL_SKIPPED:
            return ToolSkippedEvent(
                **base_event.model_dump(),
                arguments=payload.get("args"),
                tool=payload.get("tool"),
                reason=payload.get("code"),
            )

        case _:
            return None
