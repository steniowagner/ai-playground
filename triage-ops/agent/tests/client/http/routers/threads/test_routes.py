from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
import triage_ops.client.http.routers.threads.router as threads_router_module
from httpx import AsyncClient
from triage_ops.graph.event_stream import (
    MessageChunkEvent,
    ProposalRejectedEvent,
    ToolFinishedEvent,
)
from triage_ops.graph.nodes.request_approvals import ApprovalDecision

from tests.client.http.support import (
    RecordingGraphRunner,
    RecordingSampleQuestionsRepository,
    parse_sse_events,
)

pytestmark = pytest.mark.unit

THREAD_ID = UUID("10000000-0000-0000-0000-000000000001")
MESSAGE_EVENT_ID = UUID("20000000-0000-0000-0000-000000000001")
TOOL_EVENT_ID = UUID("20000000-0000-0000-0000-000000000002")
APPROVAL_EVENT_ID = UUID("20000000-0000-0000-0000-000000000003")
PROPOSAL_ID = UUID("30000000-0000-0000-0000-000000000001")


async def test_create_thread_returns_generated_identifier(
    http_client: tuple[
        AsyncClient, RecordingGraphRunner, RecordingSampleQuestionsRepository
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _, _ = http_client
    monkeypatch.setattr(
        threads_router_module,
        "create_thread_id",
        lambda: THREAD_ID,
    )

    response = await client.post("/threads/")

    assert response.status_code == 200
    assert response.json() == {"thread_id": str(THREAD_ID)}


async def test_message_stream_forwards_request_and_serializes_graph_events_as_sse(
    http_client: tuple[
        AsyncClient, RecordingGraphRunner, RecordingSampleQuestionsRepository
    ],
) -> None:
    client, graph_runner, _ = http_client
    graph_runner.start_events = [
        MessageChunkEvent(
            event_id=MESSAGE_EVENT_ID,
            thread_id=str(THREAD_ID),
            content="I found the incident.",
        ),
        ToolFinishedEvent(
            event_id=TOOL_EVENT_ID,
            thread_id=str(THREAD_ID),
            tool="get_incident",
            arguments={"incident_id": "INC-1042"},
            ok=True,
        ),
    ]

    response = await client.post(
        f"/threads/{THREAD_ID}/messages/stream",
        json={"message": "Investigate INC-1042"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert graph_runner.start_calls == [(str(THREAD_ID), "Investigate INC-1042")]
    assert parse_sse_events(response.text) == [
        {
            "id": str(MESSAGE_EVENT_ID),
            "event": "message_chunk",
            "data": {
                "event_id": str(MESSAGE_EVENT_ID),
                "thread_id": str(THREAD_ID),
                "type": "message_chunk",
                "content": "I found the incident.",
            },
        },
        {
            "id": str(TOOL_EVENT_ID),
            "event": "tool_finished",
            "data": {
                "event_id": str(TOOL_EVENT_ID),
                "thread_id": str(THREAD_ID),
                "arguments": {"incident_id": "INC-1042"},
                "tool": "get_incident",
                "type": "tool_finished",
                "ok": True,
            },
        },
    ]


async def test_approval_stream_validates_decisions_and_resumes_the_same_thread(
    http_client: tuple[
        AsyncClient, RecordingGraphRunner, RecordingSampleQuestionsRepository
    ],
) -> None:
    client, graph_runner, _ = http_client
    graph_runner.resume_events = [
        ProposalRejectedEvent(
            event_id=APPROVAL_EVENT_ID,
            thread_id=str(THREAD_ID),
            kind="restart_service",
            arguments={
                "service": "checkout-api",
                "environment": "production",
                "strategy": "rolling",
            },
            incident_id="INC-1042",
            proposal_id=PROPOSAL_ID,
        )
    ]

    response = await client.post(
        f"/threads/{THREAD_ID}/approvals/stream",
        json={"decisions": [{"proposal_id": str(PROPOSAL_ID), "approved": False}]},
    )

    assert response.status_code == 200
    assert graph_runner.resume_calls == [
        (
            str(THREAD_ID),
            [ApprovalDecision(proposal_id=PROPOSAL_ID, approved=False)],
        )
    ]
    assert parse_sse_events(response.text) == [
        {
            "id": str(APPROVAL_EVENT_ID),
            "event": "proposal_rejected",
            "data": {
                "event_id": str(APPROVAL_EVENT_ID),
                "thread_id": str(THREAD_ID),
                "kind": "restart_service",
                "arguments": {
                    "service": "checkout-api",
                    "environment": "production",
                    "strategy": "rolling",
                },
                "incident_id": "INC-1042",
                "proposal_id": str(PROPOSAL_ID),
                "result": None,
                "type": "proposal_rejected",
            },
        }
    ]


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        (
            "/threads/not-a-uuid/messages/stream",
            {"message": "Investigate INC-1042"},
        ),
        (f"/threads/{THREAD_ID}/messages/stream", {"message": ""}),
        (
            f"/threads/{THREAD_ID}/approvals/stream",
            {"decisions": [{"proposal_id": str(PROPOSAL_ID), "approved": "yes"}]},
        ),
    ],
)
async def test_invalid_route_input_returns_422_without_calling_the_graph(
    http_client: tuple[
        AsyncClient, RecordingGraphRunner, RecordingSampleQuestionsRepository
    ],
    path: str,
    payload: dict[str, Any],
) -> None:
    client, graph_runner, _ = http_client

    response = await client.post(path, json=payload)

    assert response.status_code == 422
    assert graph_runner.start_calls == []
    assert graph_runner.resume_calls == []
