from langchain.messages import (
    ToolMessage,
)
from langchain_core.messages.tool import ToolCall

from triage_ops.tools import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
)


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

    return ToolMessage(
        content=error.model_dump_json(),
        name=tool_call["name"],
        tool_call_id=tool_call["id"],
    )


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

    return ToolMessage(
        content=error.model_dump_json(),
        name=tool_call["name"],
        tool_call_id=tool_call["id"],
    )


def make_repeated_tool_call_error(tool_call: ToolCall) -> ToolMessage:
    response = ToolErrorResponse(
        ok=False,
        error=ToolErrorResponseDetail(
            code="RETRY_NOT_ALLOWED",
            message=f"Tool '{tool_call['name']}' was already called with the same arguments.",
            retryable=False,
            input=tool_call["args"],
            suggested_action="Use the existing result, make a materially different call if justified, or complete the investigation.",
        ),
    )

    return ToolMessage(
        content=response.model_dump_json(),
        name=tool_call["name"],
        tool_call_id=tool_call["id"],
    )
