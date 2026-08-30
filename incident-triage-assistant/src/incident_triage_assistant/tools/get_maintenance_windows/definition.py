from incident_triage_assistant.tools.types import Tool

from .schema import GetMaintenanceWindowsArgs

GET_MAINTENANCE_WINDOW_TOOL = Tool(
    name="get_maintenance_windows",
    description="Retrieve approved maintenance windows that overlap a requested period for one exact service and environment. Maintenance is supporting evidence, not an unconditional reason to ignore an alert or customer impact.",
    parameters=GetMaintenanceWindowsArgs.model_json_schema(),
)
