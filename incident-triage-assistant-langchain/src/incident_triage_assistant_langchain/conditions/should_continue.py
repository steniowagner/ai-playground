from typing import Literal

from incident_triage_assistant_langchain.nodes.schema import Nodes
from incident_triage_assistant_langchain.state import State


def should_continue(state: State) -> Literal[Nodes.TOOL, Nodes.FINALIZER]:
    last_message = state.messages[-1]

    if last_message.tool_calls:
        return Nodes.TOOL

    return Nodes.FINALIZER
