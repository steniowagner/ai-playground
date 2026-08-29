from incident_triage_assistant.tools.types import Tool

from .schema import GetIncidentArgs

GET_INCIDENT_TOOL: Tool = Tool(
    name="get_incident",
    description="Retrieve the recorded details of one incident by its exact incident ID, including the affected service, environment, alert, status, timestamps, and reported symptoms. Use this as the starting point when investigating a known incident.",
    parameters=GetIncidentArgs.model_json_schema(),
)
