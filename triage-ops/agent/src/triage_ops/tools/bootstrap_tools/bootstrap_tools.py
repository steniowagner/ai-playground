from langchain_core.tools import BaseTool

from triage_ops.tools.complete_investigation.tool import CompleteInvestigationTool
from triage_ops.tools.get_feature_flags.tool import GetFeatureFlagsTool
from triage_ops.tools.get_incident.tool import GetIncidentTool
from triage_ops.tools.get_incidents import GetIncidentsTool
from triage_ops.tools.get_maintenance_windows.tool import GetMaintenanceWindowsTool
from triage_ops.tools.get_recent_deployments.tool import GetRecentDeploymentsTool
from triage_ops.tools.get_runbook.tool import GetRunbookTool
from triage_ops.tools.get_service_context.tool import GetServiceContextTool
from triage_ops.tools.query_logs.tool import QueryLogsTool
from triage_ops.tools.query_metrics.tool import QueryMetricsTool

from .schema import BootstrapToolsArgs


def bootstrap_tools(args: BootstrapToolsArgs) -> list[BaseTool]:
    return [
        GetIncidentTool(repository=args.incidents_repository),
        GetIncidentsTool(repository=args.incidents_repository),
        GetFeatureFlagsTool(repository=args.feature_flags_repository),
        GetMaintenanceWindowsTool(repository=args.maintenance_windows_repository),
        GetRecentDeploymentsTool(repository=args.deployments_repository),
        GetRunbookTool(repository=args.runbooks_repository),
        GetServiceContextTool(repository=args.services_repository),
        QueryLogsTool(repository=args.logs_repository),
        QueryMetricsTool(repository=args.metrics_repository),
        CompleteInvestigationTool(),
    ]
