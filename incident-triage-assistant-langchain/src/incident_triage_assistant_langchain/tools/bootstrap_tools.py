from incident_triage_assistant_langchain.repositories.feature_flags.json import (
    JSONFeatureFlagsRepository,
)
from incident_triage_assistant_langchain.repositories.incidents.json import (
    JSONIncidentRepository,
)
from incident_triage_assistant_langchain.repositories.maintenance_windows.json import (
    JSONMaintenanceWindowsRepository,
)
from langchain_core.tools import BaseTool

from .get_feature_flags.tool import GetFeatureFlagsTool
from .get_incident.tool import GetIncidentTool
from .get_maintenance_windows.tool import GetMaintenanceWindowsTool


def bootstrap_tools() -> list[BaseTool]:
    json_incidents_repository = JSONIncidentRepository()
    json_feature_flags_repository = JSONFeatureFlagsRepository()
    json_maintenance_windows_repository = JSONMaintenanceWindowsRepository()

    tools = [
        GetIncidentTool(repository=json_incidents_repository),
        GetFeatureFlagsTool(repository=json_feature_flags_repository),
        GetMaintenanceWindowsTool(repository=json_maintenance_windows_repository),
    ]

    return tools
