from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from triage_ops.graph import GraphRunner

from ..schema import GraphRequest, GraphResponse

router = APIRouter(prefix="/graph", tags=["graph"])


def get_graph_runner(request: Request) -> GraphRunner:
    return request.app.state.graph_runner


GraphRunnerDependency = Annotated[GraphRunner, Depends(get_graph_runner)]


@router.post("/")
def start(request: GraphRequest, graph_runner: GraphRunnerDependency) -> GraphResponse:
    thread_id = request.thread_id or uuid4()

    answer = graph_runner.start(thread_id=thread_id, message=request.message)

    return GraphResponse(
        thread_id=thread_id,
        content=answer.content,
    )
