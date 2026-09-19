from typing import Literal

from langchain.messages import AIMessage
from langgraph.graph import END

from triage_ops.graph import State
from triage_ops.graph.nodes import Nodes


def after_llm_call(state: State) -> Literal[Nodes.TOOL, "__end__"]:
    if not state.messages:
        return END

    last_message = state.messages[-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return Nodes.TOOL

    return END
