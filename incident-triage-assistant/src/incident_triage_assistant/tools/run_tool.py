import json
from collections.abc import Callable
from typing import Any

from .get_incident.tool import get_incident
from .get_service_context.tool import get_service_context
from .tool_response import ToolErrorResponse, ToolErrorResponseDetail, ToolResponse


def get_tool(tool_name: str) -> Callable[[dict[str, Any]], ToolResponse] | None:
    match tool_name:
        case "get_incident":
            return get_incident
        case "get_service_context":
            return get_service_context
        case _:
            return None


def run_tool(tool_name: str, json_str_args: str) -> ToolResponse:
    run = get_tool(tool_name)

    if run is None:
        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="UNKNOWN_TOOL",
                message=f"Unknown tool '{tool_name}'.",
            ),
        )

    try:
        args = json.loads(json_str_args)
    except json.JSONDecodeError:
        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="INVALID_ARGUMENT",
                message=f"Invalid tool arguments '{json_str_args}'.",
            ),
        )

    return run(args)
