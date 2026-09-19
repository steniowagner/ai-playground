from typing import Literal

from triage_ops.graph.event_stream import (
    GraphEvent,
    MessageChunkEvent,
    ModelThinkingEvent,
)


def handle_message_event(
    event: GraphEvent,
    message_utils: dict[
        Literal["previous_message_event"], ModelThinkingEvent | MessageChunkEvent | None
    ],
) -> None:
    if not event.content:
        return

    if isinstance(event, ModelThinkingEvent) and not isinstance(
        message_utils["previous_message_event"], ModelThinkingEvent
    ):
        print("\n[Thinking]\n")

    if isinstance(event, MessageChunkEvent) and not isinstance(
        message_utils["previous_message_event"], MessageChunkEvent
    ):
        print("\n\n[Answer]\n")

    message_utils["previous_message_event"] = event

    print(event.content, end="", flush=True)
