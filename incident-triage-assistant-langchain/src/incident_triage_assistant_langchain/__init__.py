import asyncio

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

from incident_triage_assistant_langchain.client.cli.run_cli import run_cli
from incident_triage_assistant_langchain.graph.builder import build_graph
from incident_triage_assistant_langchain.graph.runner.graph_runner import (
    GraphRunner,
)
from incident_triage_assistant_langchain.model.factory import create_model


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
