from langchain_core.tools import BaseTool

from triage_ops.repositories.deployments.json import (
    JSONDeploymentsRepository,
)
from triage_ops.repositories.feature_flags.json import (
    JSONFeatureFlagsRepository,
)
from triage_ops.repositories.incidents.json import (
    JSONIncidentRepository,
)
from triage_ops.repositories.logs.json import (
    JSONLogsRepository,
)
from triage_ops.repositories.maintenance_windows.json import (
    JSONMaintenanceWindowsRepository,
)
from triage_ops.repositories.metrics.json import (
    JSONMetricsRepository,
)
from triage_ops.repositories.runbooks.json import (
    JSONRunbooksRepository,
)
from triage_ops.repositories.services.json import (
    JSONServicesRepository,
)

from .complete_investigation.tool import CompleteInvestigationTool
from .get_feature_flags.tool import GetFeatureFlagsTool
from .get_incident.tool import GetIncidentTool
from .get_maintenance_windows.tool import GetMaintenanceWindowsTool
from .get_recent_deployments.tool import GetRecentDeploymentsTool
from .get_runbook.tool import GetRunbookTool
from .get_service_context.tool import GetServiceContextTool
from .query_logs.tool import QueryLogsTool
from .query_metrics.tool import QueryMetricsTool


def bootstrap_tools() -> list[BaseTool]:
    json_incidents_repository = JSONIncidentRepository()
    json_feature_flags_repository = JSONFeatureFlagsRepository()
    json_maintenance_windows_repository = JSONMaintenanceWindowsRepository()
    json_deployment_repository = JSONDeploymentsRepository()
    json_runbooks_repository = JSONRunbooksRepository()
    json_service_repository = JSONServicesRepository()
    json_logs_repository = JSONLogsRepository()
    json_metrics_repository = JSONMetricsRepository()

    tools = [
        GetIncidentTool(repository=json_incidents_repository),
        GetFeatureFlagsTool(repository=json_feature_flags_repository),
        GetMaintenanceWindowsTool(repository=json_maintenance_windows_repository),
        GetRecentDeploymentsTool(repository=json_deployment_repository),
        GetRunbookTool(repository=json_runbooks_repository),
        GetServiceContextTool(repository=json_service_repository),
        QueryLogsTool(repository=json_logs_repository),
        QueryMetricsTool(repository=json_metrics_repository),
        CompleteInvestigationTool(),
    ]

    return tools
