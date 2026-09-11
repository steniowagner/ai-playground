import json

from .schema import StreamEvents


def handle_custom_event(payload: dict) -> None:
    event = payload.get("event")

    if event == StreamEvents.TOOL_STARTED:
        args = json.dumps(
            payload["args"],
            sort_keys=True,
        )

        print(
            f"{payload['tool']} {args}",
            flush=True,
        )

    elif event == StreamEvents.TOOL_FINISHED:
        mark = "ok" if payload["ok"] else payload["code"]

        print(
            f"      → {mark}",
            flush=True,
        )

    elif event in (
        StreamEvents.TOOL_FAILED,
        StreamEvents.TOOL_SKIPPED,
    ):
        print(
            f"      → {payload.get('code') or payload.get('reason')}",
            flush=True,
        )
