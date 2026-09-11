from typing import Any

from incident_triage_assistant_langchain.nodes.schema import Nodes


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


def handle_message_event(payload: dict) -> None:
    message_chunk, metadata = payload

    node = metadata.get("langgraph_node")

    if node not in (
        Nodes.LLM_CALL,
        Nodes.FINALIZER,
    ):
        return

    thinking, answer = split_stream_chunk(message_chunk)

    if thinking:
        print(
            f"[Thinking] {thinking}",
            end="",
            flush=True,
        )
        print()

    if answer:
        print(
            f"[Answer] {answer}",
            end="",
            flush=True,
        )
        print()
