from typing import Any

from langchain.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.messages.tool import ToolCall
from pydantic import TypeAdapter

from triage_ops.tools.schema import (
    ToolErrorResponse,
    ToolSuccessResponse,
)

MAX_TOOL_CALLS_ALLOWED = 2

TOOL_RESPONSE_ADAPTER = TypeAdapter(ToolSuccessResponse[Any] | ToolErrorResponse)


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
