import json

from .get_incident.definition import GET_INCIDENT_TOOL
from .get_incident.tool import get_incident
from .types import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolRegistration,
    ToolResponse,
)

TOOLS_REGISTRATIONS = (
    ToolRegistration(
        definition=GET_INCIDENT_TOOL,
        handler=get_incident,
    ),
)


class ToolsRegistry:
    def __init__(self) -> None:
        self._tools = {
            tool_registration.definition.name: tool_registration
            for tool_registration in TOOLS_REGISTRATIONS
        }

    def get_registrations(self) -> list[ToolRegistration]:
        return [tool for _, tool in self._tools.items()]

    def execute_tool(self, tool_name: str, raw_args: str) -> ToolResponse:
        tool = self._tools.get(tool_name, None)
        if tool is None:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="UNKNOWN_TOOL",
                    message=f"Unknown tool '{tool_name}'.",
                ),
            )

        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="INVALID_ARGUMENT",
                    message=f"Invalid tool arguments '{raw_args}'.",
                ),
            )

        return tool.handler(args)
