import re

from incident_triage_assistant_langchain.graph.event_stream.schema import (
    CustomStreamEvents,
)
from incident_triage_assistant_langchain.graph.state import State
from incident_triage_assistant_langchain.tools.schema import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolNames,
)
from langchain.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.messages.tool import ToolCall
from langchain_core.tools import BaseTool
from langgraph.config import get_stream_writer
from pydantic import ValidationError

from .errors import (
    make_repeated_tool_call_error,
    make_tool_invocation_error,
    make_tool_not_found_error,
)
from .schema import ToolCallStreamEventCodes
from .utils import (
    should_allow_tool_call,
)

INCIDENT_ID_PATTERN = re.compile(r"(?<![A-Za-z0-9_-])INC-\d{4}(?![A-Za-z0-9_-])")


def latest_user_incident_ids(state: State) -> set[str]:
    for message in reversed(state.messages):
        if isinstance(message, HumanMessage):
            return set(INCIDENT_ID_PATTERN.findall(message.text))

    return set()


def is_authorized_incident_lookup(state: State, tool_call: ToolCall) -> bool:
    if tool_call["name"] != ToolNames.GET_INCIDENT:
        return True

    supplied_ids = latest_user_incident_ids(state)
    requested_id = tool_call["args"].get("incident_id")

    return requested_id in supplied_ids


def make_get_incident_error_response(tool_call: ToolCall) -> ToolMessage:
    response = ToolErrorResponse(
        ok=False,
        error=ToolErrorResponseDetail(
            code="INVALID_ARGUMENT",
            message="The incident ID was not explicitly provided in the latest user message.",
            retryable=False,
            input=tool_call["args"],
            suggested_action="Ask the user to provide an incident ID in the exact INC-XXXX format. Do not infer or normalize it.",
        ),
    )

    return ToolMessage(
        content=response.model_dump_json(),
        name=tool_call["name"],
        tool_call_id=tool_call["id"],
    )


def tool_calls_node(state: State, *, tools: dict[str, BaseTool]) -> dict:
    last_message = state.messages[-1]

    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}

    tool_call_results: list[ToolMessage] = []
    write_stream_event = get_stream_writer()

    for tool_call in last_message.tool_calls:
        if not is_authorized_incident_lookup(state, tool_call):
            tool_call_results.append(make_get_incident_error_response(tool_call))

            write_stream_event(
                {
                    "event": CustomStreamEvents.TOOL_SKIPPED,
                    "tool": tool_call["name"],
                    "args": tool_call["args"],
                    "code": ToolCallStreamEventCodes.INCIDENT_ID_NOT_PROVIDED,
                }
            )

            continue

        write_stream_event(
            {
                "event": CustomStreamEvents.TOOL_STARTED,
                "tool": tool_call["name"],
                "args": tool_call["args"],
            }
        )

        messages = [*state.messages, *tool_call_results]
        if not should_allow_tool_call(messages, tool_call):
            write_stream_event(
                {
                    "event": CustomStreamEvents.TOOL_SKIPPED,
                    "tool": tool_call["name"],
                    "args": tool_call["args"],
                    "code": ToolCallStreamEventCodes.REPEATED_TOOL_CALL,
                }
            )
            tool_call_results.append(make_repeated_tool_call_error(tool_call))
            continue

        tool = tools.get(tool_call["name"], None)
        if tool is None:
            write_stream_event(
                {
                    "event": CustomStreamEvents.TOOL_FAILED,
                    "tool": tool_call["name"],
                    "args": tool_call["args"],
                    "code": ToolCallStreamEventCodes.UNKNOWN_TOOL,
                }
            )
            tool_call_results.append(make_tool_not_found_error(tool_call))
            continue

        try:
            if tool.args_schema is not None:
                tool.args_schema.model_validate(tool_call["args"])
        except ValidationError:
            write_stream_event(
                {
                    "event": CustomStreamEvents.TOOL_FAILED,
                    "tool": tool_call["name"],
                    "args": tool_call["args"],
                    "code": ToolCallStreamEventCodes.INVALID_ARGUMENTS,
                }
            )
            tool_call_results.append(make_tool_invocation_error(tool_call))
            continue

        result = tool.invoke(tool_call["args"])

        write_stream_event(
            {
                "event": CustomStreamEvents.TOOL_FINISHED,
                "tool": tool_call["name"],
                "ok": result.ok,
                "code": None if result.ok else result.error.code,
                "args": tool_call["args"],
            }
        )

        tool_call_results.append(
            ToolMessage(
                content=result.model_dump_json(),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )

    return {"messages": tool_call_results}
