from typing import Any

from langchain.messages import AIMessageChunk

from ..nodes.schema import Nodes
from .schema import Event, MessageChunkEvent, ModelThinkingEvent


def split_stream_chunk(message_chunk: str | Any) -> tuple[str, str]:
    content = message_chunk.content

    if isinstance(content, str):
        return "", content

    thinking_parts: list[str] = []
    answer_parts: list[str] = []

    for block in content:
        if not isinstance(block, dict):
            continue

        block_type = block.get("type")

        if block_type in ("thinking", "reasoning"):
            thinking_parts.append(block.get("thinking") or block.get("reasoning") or "")
        if block_type == "text":
            answer_parts.append(block.get("text", ""))

    return "".join(thinking_parts), "".join(answer_parts)


def parse_message_event(
    payload: Any, base_event: Event
) -> ModelThinkingEvent | MessageChunkEvent | None:
    message_chunk, metadata = payload

    if not isinstance(message_chunk, AIMessageChunk):
        return None

    if metadata.get("langgraph_node") == Nodes.FINALIZER:
        return None

    thinking, answer = split_stream_chunk(message_chunk)

    if thinking:
        return ModelThinkingEvent(
            **base_event.model_dump(),
            content=thinking,
        )

    if answer:
        return MessageChunkEvent(
            **base_event.model_dump(),
            content=answer,
        )
