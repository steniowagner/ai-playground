import json

from .get_feature_flags.definition import GET_FEATURE_FLAGS_TOOL
from .get_feature_flags.tool import get_feature_flags
from .get_incident.definition import GET_INCIDENT_TOOL
from .get_incident.tool import get_incident
from .get_maintenance_windows.definition import GET_MAINTENANCE_WINDOW_TOOL
from .get_maintenance_windows.tool import get_maintenance_windows
from .get_recent_deployments.definition import GET_RECENT_DEPLOYMENTS_TOOL
from .get_recent_deployments.tool import get_recent_deployments
from .get_runbook.definition import GET_RUNBOOK_TOOL
from .get_runbook.tool import get_runbook
from .get_service_context.definition import GET_SERVICE_CONTEXT_TOOL
from .get_service_context.tool import get_service_context
from .query_logs.definition import QUERY_LOGS_TOOL
from .query_logs.tool import query_logs
from .query_metrics.definition import QUERY_METRICS_TOOL
from .query_metrics.tool import query_metrics
from .types import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolRegistration,
    ToolResponse,
)

TOOLS_REGISTRATIONS = (
    ToolRegistration(
        definition=GET_FEATURE_FLAGS_TOOL,
        handler=get_feature_flags,
    ),
    ToolRegistration(
        definition=GET_INCIDENT_TOOL,
        handler=get_incident,
    ),
    ToolRegistration(
        definition=GET_MAINTENANCE_WINDOW_TOOL,
        handler=get_maintenance_windows,
    ),
    ToolRegistration(
        definition=GET_RECENT_DEPLOYMENTS_TOOL,
        handler=get_recent_deployments,
    ),
    ToolRegistration(
        definition=GET_RUNBOOK_TOOL,
        handler=get_runbook,
    ),
    ToolRegistration(
        definition=GET_SERVICE_CONTEXT_TOOL,
        handler=get_service_context,
    ),
    ToolRegistration(
        definition=QUERY_LOGS_TOOL,
        handler=query_logs,
    ),
    ToolRegistration(
        definition=QUERY_METRICS_TOOL,
        handler=query_metrics,
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
