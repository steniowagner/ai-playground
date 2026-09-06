from typing import Any

from incident_triage_assistant_langchain.state import State
from incident_triage_assistant_langchain.tools.schema import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolSuccessResponse,
)
from langchain.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.messages.tool import ToolCall
from langchain_core.tools import BaseTool
from pydantic import TypeAdapter, ValidationError

MAX_TOOL_CALLS_ALLOWED = 2

TOOL_RESPONSE_ADAPTER = TypeAdapter(ToolSuccessResponse[Any] | ToolErrorResponse)


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
        tool_call_id=tool_call["id"],
    )


def find_messages_since_last_human_message(
    messages: list[AnyMessage],
) -> list[AnyMessage]:
    for index in range(len(messages) - 1, -1, -1):
        if isinstance(messages[index], HumanMessage):
            return messages[index:]

    return messages


def find_matching_tool_results(
    messages: list[AnyMessage], tool_call: ToolCall
) -> list[ToolMessage]:
    current_investigation_messages = find_messages_since_last_human_message(messages)

    results_by_call_id: dict[str, ToolMessage] = {
        message.tool_call_id: message
        for message in current_investigation_messages
        if isinstance(message, ToolMessage)
    }

    matching_results: list[ToolMessage] = []

    for message in current_investigation_messages:
        if not isinstance(message, AIMessage):
            continue

        for previous_tool_call in message.tool_calls:
            if (
                previous_tool_call["name"] == tool_call["name"]
                and previous_tool_call["args"] == tool_call["args"]
            ):
                result = results_by_call_id.get(previous_tool_call["id"], None)
                if result is not None:
                    matching_results.append(result)

    return matching_results


def should_allow_tool_call(
    messages: list[AnyMessage],
    tool_call: ToolCall,
) -> bool:
    """
    In order to prevent tool-call infinity loops...
    1. No previous identical call -> allow it.
    2. Previous identical call succeeded -> reject repetition.
    3. Previous identical call failed with retryable=false -> reject repetition.
    4. One previous identical retryable failure -> allow one retry.
    5. Two previous identical attempts -> reject further repetition.
    """

    previous_results = find_matching_tool_results(messages, tool_call)

    executed_results = [
        message
        for message in previous_results
        if TOOL_RESPONSE_ADAPTER.validate_json(message.content).error is None
        or TOOL_RESPONSE_ADAPTER.validate_json(message.content).error.code
        != "RETRY_NOT_ALLOWED"
    ]

    if not executed_results:
        return True

    if len(executed_results) >= MAX_TOOL_CALLS_ALLOWED:
        return False

    response = TOOL_RESPONSE_ADAPTER.validate_json(executed_results[-1].content)

    return not response.ok and response.error.retryable


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
