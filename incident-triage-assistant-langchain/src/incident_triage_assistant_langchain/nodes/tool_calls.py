from incident_triage_assistant_langchain.state import State
from langchain.messages import ToolMessage
from langchain_core.tools import BaseTool


def tool_calls_node(state: State, *, tools: dict[str, BaseTool]) -> dict:
    tool_calls_results = []

    for tool_call in state.messages[-1].tool_calls:
        tool = tools[tool_call["name"]]
        result = tool.invoke(tool_call["args"])
        tool_calls_results.append(
            ToolMessage(content=result, tool_call_id=tool_call["id"])
        )

    return {"messages": tool_calls_results}
