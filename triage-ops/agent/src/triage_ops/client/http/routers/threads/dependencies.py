from fastapi import Request
from triage_ops.graph import GraphRunner


def get_graph_runner(request: Request) -> GraphRunner:
    return request.app.state.graph_runner
