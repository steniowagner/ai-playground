from incident_triage_assistant_langchain.state import State
from incident_triage_assistant_langchain.tools.schema import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
)
from langchain.messages import ToolMessage
from langchain_core.messages.tool import ToolCall
from langchain_core.tools import BaseTool
from pydantic import ValidationError


def make_tool_not_found_error(tool_call: ToolCall) -> ToolMessage:
    error = ToolErrorResponse(
        ok=False,
        error=ToolErrorResponseDetail(
            code="UNKNOWN_TOOL",
            message=f"Tool '{tool_call['name']}' is not available.",
            retryable=False,
            input={"tool_name": tool_call["name"]},
            suggested_action="Choose one of the available tools.",
        ),
    )

    return ToolMessage(content=error.model_dump_json(), tool_call_id=tool_call["id"])


def make_tool_invocation_error(tool_call: ToolCall) -> ToolMessage:
    error = ToolErrorResponse(
        ok=False,
        error=ToolErrorResponseDetail(
            code="INVALID_ARGUMENT",
            message=f"Invalid arguments for the tool {tool_call['name']}.",
            retryable=False,
            input=tool_call["args"],
            suggested_action="Do not retry with the same arguments. Correct the arguments using the tool's input schema, then make a new request.",
        ),
    )

    return ToolMessage(content=error.model_dump_json(), tool_call_id=tool_call["id"])


def tool_calls_node(state: State, *, tools: dict[str, BaseTool]) -> dict:
    tool_calls_results = []

    for tool_call in state.messages[-1].tool_calls:
        tool = tools.get(tool_call["name"], None)
        if tool is None:
            error = make_tool_not_found_error(tool_call)
            tool_calls_results.append(error)
            continue

        try:
            if tool.args_schema is not None:
                tool.args_schema.model_validate(tool_call["args"])
        except ValidationError:
            tool_calls_results.append(make_tool_invocation_error(tool_call))
            continue

        result = tool.invoke(tool_call["args"])

        tool_calls_results.append(
            ToolMessage(content=result.model_dump_json(), tool_call_id=tool_call["id"])
        )

    return {"messages": tool_calls_results}
