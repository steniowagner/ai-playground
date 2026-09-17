from typing import Any

from pydantic import ValidationError

from triage_ops.graph.event_stream import (
    CustomStreamEvents,
)

from .schema import (
    Event,
    GraphEvent,
    MessageChunkEvent,
    ToolFailedEvent,
    ToolFinishedEvent,
    ToolSkippedEvent,
    ToolStartedEvent,
)


def parse_custom_event(payload: Any, base_event: Event) -> GraphEvent | None:
    if not isinstance(payload, dict):
        return None

    try:
        match payload.get("event"):
            case CustomStreamEvents.MESSAGE_CHUNK:
                return MessageChunkEvent(
                    **base_event.model_dump(),
                    content=payload.get("content"),
                )
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
    except ValidationError:
        return None
