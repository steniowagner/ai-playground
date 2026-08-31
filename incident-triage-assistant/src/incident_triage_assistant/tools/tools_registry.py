import json

from incident_triage_assistant.repositories.deployments.base import (
    DeploymentsRepository,
)
from incident_triage_assistant.repositories.feature_flags.base import (
    FeatureFlagsRepository,
)
from incident_triage_assistant.repositories.incidents.base import IncidentRepository
from incident_triage_assistant.repositories.logs.base import LogsRepository
from incident_triage_assistant.repositories.maintenance_windows.base import (
    MaintenanceWindowsRepository,
)
from incident_triage_assistant.repositories.metrics.base import MetricsRepository
from incident_triage_assistant.repositories.runbooks.base import RunbooksRepository
from incident_triage_assistant.repositories.services.base import ServicesRepository

from .get_feature_flags.definition import GET_FEATURE_FLAGS_TOOL
from .get_feature_flags.tool import GetFeatureFlagsTool
from .get_incident.definition import GET_INCIDENT_TOOL
from .get_incident.tool import GetIncidentTool
from .get_maintenance_windows.definition import GET_MAINTENANCE_WINDOW_TOOL
from .get_maintenance_windows.tool import GetMaintenanceWindowsTool
from .get_recent_deployments.definition import GET_RECENT_DEPLOYMENTS_TOOL
from .get_recent_deployments.tool import GetRecentDeploymentsTool
from .get_runbook.definition import GET_RUNBOOK_TOOL
from .get_runbook.tool import GetRunbookTool
from .get_service_context.definition import GET_SERVICE_CONTEXT_TOOL
from .get_service_context.tool import GetServiceContextTool
from .query_logs.definition import QUERY_LOGS_TOOL
from .query_logs.tool import QueryLogsTool
from .query_metrics.definition import QUERY_METRICS_TOOL
from .query_metrics.tool import QueryMetricsTool
from .types import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolRegistration,
    ToolResponse,
)


class ToolsRegistry:
    def __init__(
        self,
        incident_repository: IncidentRepository,
        service_repository: ServicesRepository,
        feature_flags_repository: FeatureFlagsRepository,
        maintenance_windows_repository: MaintenanceWindowsRepository,
        deployments_repository: DeploymentsRepository,
        runbooks_repository: RunbooksRepository,
        logs_repository: LogsRepository,
        metrics_repository: MetricsRepository,
    ) -> None:
        TOOLS_REGISTRATIONS = (
            ToolRegistration(
                definition=GET_FEATURE_FLAGS_TOOL,
                handler=GetFeatureFlagsTool(repository=feature_flags_repository),
            ),
            ToolRegistration(
                definition=GET_INCIDENT_TOOL,
                handler=GetIncidentTool(repository=incident_repository),
            ),
            ToolRegistration(
                definition=GET_MAINTENANCE_WINDOW_TOOL,
                handler=GetMaintenanceWindowsTool(
                    repoistory=maintenance_windows_repository
                ),
            ),
            ToolRegistration(
                definition=GET_RECENT_DEPLOYMENTS_TOOL,
                handler=GetRecentDeploymentsTool(repository=deployments_repository),
            ),
            ToolRegistration(
                definition=GET_RUNBOOK_TOOL,
                handler=GetRunbookTool(repository=runbooks_repository),
            ),
            ToolRegistration(
                definition=GET_SERVICE_CONTEXT_TOOL,
                handler=GetServiceContextTool(repository=service_repository),
            ),
            ToolRegistration(
                definition=QUERY_LOGS_TOOL,
                handler=QueryLogsTool(repository=logs_repository),
            ),
            ToolRegistration(
                definition=QUERY_METRICS_TOOL,
                handler=QueryMetricsTool(repository=metrics_repository),
            ),
        )

        self._tools = {
            tool_registration.definition.name: tool_registration
            for tool_registration in TOOLS_REGISTRATIONS
        }

    def get_definitions(self) -> list[ToolRegistration]:
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
