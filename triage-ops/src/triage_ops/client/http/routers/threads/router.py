from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.sse import EventSourceResponse, ServerSentEvent
from triage_ops.client.http.utils import create_thread_id, get_graph_runner
from triage_ops.graph import GraphRunner

from .schema import CreateThreadResponse, StartThreadRequest

router = APIRouter(prefix="/threads", tags=["threads"])


GraphRunnerDependency = Annotated[GraphRunner, Depends(get_graph_runner)]


@router.post("/")
def create_thread() -> CreateThreadResponse:
    return CreateThreadResponse(thread_id=create_thread_id())


@router.post("/{thread_id}/messages/stream", response_class=EventSourceResponse)
async def stream_messages(
    thread_id: UUID, request: StartThreadRequest, graph_runner: GraphRunnerDependency
) -> AsyncGenerator[ServerSentEvent]:
    async for graph_event in graph_runner.start(
        thread_id=str(thread_id), message=request.message
    ):
        yield ServerSentEvent(
            id=str(graph_event.event_id),
            event=graph_event.type,
            data=graph_event.model_dump(mode="json"),
        )
