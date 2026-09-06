from incident_triage_assistant_langchain.state import State
from langchain.messages import (
    ToolMessage,
)
from langchain_core.tools import BaseTool
from pydantic import ValidationError

from .errors import (
    make_repeated_tool_call_error,
    make_tool_invocation_error,
    make_tool_not_found_error,
)
from .utils import (
    should_allow_tool_call,
)


def tool_calls_node(state: State, *, tools: dict[str, BaseTool]) -> dict:
    tool_call_results: list[ToolMessage] = []

    for tool_call in state.messages[-1].tool_calls:
        messages = [*state.messages, *tool_call_results]
        if not should_allow_tool_call(messages, tool_call):
            tool_call_results.append(make_repeated_tool_call_error(tool_call))
            continue

        tool = tools.get(tool_call["name"], None)
        if tool is None:
            error = make_tool_not_found_error(tool_call)
            tool_call_results.append(error)
            continue

        try:
            if tool.args_schema is not None:
                tool.args_schema.model_validate(tool_call["args"])
        except ValidationError:
            tool_call_results.append(make_tool_invocation_error(tool_call))
            continue

        result = tool.invoke(tool_call["args"])

        tool_call_results.append(
            ToolMessage(
                content=result.model_dump_json(),
                tool_call_id=tool_call["id"],
            )
        )

    return {"messages": tool_call_results}
