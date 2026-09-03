from typing import Literal

from incident_triage_assistant_langchain.nodes.schema import Nodes
from incident_triage_assistant_langchain.state import State
from langgraph.graph import END


def should_continue(state: State) -> Literal[Nodes.TOOL, END]:
    last_message = state.messages[-1]

    if last_message.tool_calls:
        return Nodes.TOOL

    return END
