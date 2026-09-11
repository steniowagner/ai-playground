from incident_triage_assistant_langchain.graph.state import State
from incident_triage_assistant_langchain.graph.stream.schema import StreamEvents
from langchain.messages import (
    AIMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langgraph.config import get_stream_writer
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
    last_message = state.messages[-1]

    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}

    tool_call_results: list[ToolMessage] = []
    write_stream_event = get_stream_writer()

    for tool_call in last_message.tool_calls:
        write_stream_event(
            {
                "event": StreamEvents.TOOL_STARTED,
                "tool": tool_call["name"],
                "args": tool_call["args"],
            }
        )

        messages = [*state.messages, *tool_call_results]
        if not should_allow_tool_call(messages, tool_call):
            write_stream_event(
                {
                    "event": StreamEvents.TOOL_SKIPPED,
                    "tool": tool_call["name"],
                    "args": tool_call["args"],
                    "code": "repeated_tool_call",
                }
            )
            tool_call_results.append(make_repeated_tool_call_error(tool_call))
            continue

        tool = tools.get(tool_call["name"], None)
        if tool is None:
            write_stream_event(
                {
                    "event": StreamEvents.TOOL_FAILED,
                    "tool": tool_call["name"],
                    "args": tool_call["args"],
                    "code": "unknown_tool",
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
                    "event": StreamEvents.TOOL_FAILED,
                    "tool": tool_call["name"],
                    "args": tool_call["args"],
                    "code": "invalid_arguments",
                }
            )
            tool_call_results.append(make_tool_invocation_error(tool_call))
            continue

        result = tool.invoke(tool_call["args"])

        write_stream_event(
            {
                "event": StreamEvents.TOOL_FINISHED,
                "tool": tool_call["name"],
                "ok": result.ok,
                "code": None if result.ok else result.error.code,
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
