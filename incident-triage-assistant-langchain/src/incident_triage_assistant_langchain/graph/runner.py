from collections.abc import AsyncIterator
from typing import Any, TypeAlias

from incident_triage_assistant_langchain.graph.nodes.request_approvals.schema import (
    ApprovalDecision,
)
from langchain.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from .event_stream.parse_graph_event import parse_graph_event
from .event_stream.schema import GraphEvent, ParseGraphEventArgs

GraphInput: TypeAlias = dict[str, Any] | Command


class GraphRunner:
    def __init__(self, graph: CompiledStateGraph) -> None:
        self._graph = graph

    async def _stream(
        self,
        thread_id: str,
        graph_input: GraphInput,
    ) -> AsyncIterator[GraphEvent]:
        config: RunnableConfig = {
            "configurable": {"thread_id": thread_id},
        }

        async for mode, payload in self._graph.astream(
            input=graph_input,
            config=config,
            stream_mode=["messages", "updates", "custom"],
        ):
            for event in parse_graph_event(
                ParseGraphEventArgs(mode=mode, payload=payload, thread_id=thread_id)
            ):
                yield event

    async def start(self, thread_id: str, message: str) -> AsyncIterator[GraphEvent]:
        graph_input: GraphInput = {
            "messages": [HumanMessage(content=message)],
            "final_result": None,
        }

        async for event in self._stream(thread_id, graph_input):
            yield event

    async def resume(
        self,
        thread_id: str,
        decisions: list[ApprovalDecision],
    ) -> AsyncIterator[GraphEvent]:
        command = Command(
            resume={
                "decisions": [
                    decision.model_dump(mode="json") for decision in decisions
                ]
            }
        )

        async for event in self._stream(thread_id, command):
            yield event
