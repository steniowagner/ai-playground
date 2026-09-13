from typing import Literal

from incident_triage_assistant_langchain.graph.nodes.schema import Nodes
from incident_triage_assistant_langchain.graph.state import State
from langchain.messages import AIMessage
from langgraph.graph import END


def after_llm_call(state: State) -> Literal[Nodes.TOOL, "__end__"]:
    last_message = state.messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return Nodes.TOOL

    return END
