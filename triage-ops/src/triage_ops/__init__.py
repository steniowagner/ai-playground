import asyncio

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

from triage_ops.client.cli import run_cli
from triage_ops.graph import (
    GraphRunner,
    build_graph,
)
from triage_ops.model import create_model


def main() -> None:
    load_dotenv()

    model = create_model("anthropic")
    checkpointer = InMemorySaver()
    graph = build_graph(model, checkpointer)
    graph_runner = GraphRunner(graph)

    asyncio.run(
        run_cli(
            graph_runner=graph_runner,
            thread_id="cli",
        )
    )


__all__ = ["main"]
