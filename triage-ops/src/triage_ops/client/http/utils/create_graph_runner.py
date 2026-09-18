from langgraph.checkpoint.memory import InMemorySaver
from triage_ops.graph import (
    GraphRunner,
    build_graph,
)
from triage_ops.model import create_model


def create_graph_runner() -> GraphRunner:
    model = create_model("anthropic")
    checkpointer = InMemorySaver()
    graph = build_graph(model, checkpointer)
    return GraphRunner(graph)
