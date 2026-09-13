from typing import Literal

from incident_triage_assistant_langchain.graph.nodes.schema import Nodes
from incident_triage_assistant_langchain.graph.state import State
from incident_triage_assistant_langchain.tools.schema import (
    ToolNames,
)
from langchain.messages import ToolMessage


def after_tool_call(state: State) -> Literal[Nodes.LLM_CALL, Nodes.FINALIZER]:
    for message in reversed(state.messages):
        if not isinstance(message, ToolMessage):
            break

        if message.name == ToolNames.COMPLETE_INVESTIGATION:
            return Nodes.FINALIZER

    return Nodes.LLM_CALL
