from incident_triage_assistant.domain.types import Tool

from .schema import GetMaintenanceWindowsArgs

GET_MAINTENANCE_WINDOW_TOOL: Tool = {
    "name": "get_maintenance_windows",
    "description": "Determine whether observed behavior falls within approved maintenance.",
    "parameters": GetMaintenanceWindowsArgs.model_json_schema(),
}
