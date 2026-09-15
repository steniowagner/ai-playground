from typing import Literal

from langchain.messages import ToolMessage
from triage_ops.graph.nodes.schema import Nodes
from triage_ops.graph.state import State
from triage_ops.tools.schema import (
    ToolNames,
)


def after_tool_call(state: State) -> Literal[Nodes.LLM_CALL, Nodes.FINALIZER]:
    for message in reversed(state.messages):
        if not isinstance(message, ToolMessage):
            break

        if message.name == ToolNames.COMPLETE_INVESTIGATION:
            return Nodes.FINALIZER

    return Nodes.LLM_CALL
