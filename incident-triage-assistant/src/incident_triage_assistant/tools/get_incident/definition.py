from incident_triage_assistant.tools.get_tools import Tool

from .schema import GetIncidentArgs

GET_INCIDENT_TOOL: Tool = {
    "name": "get_incident",
    "description": "Get an incident by its exact ID.",
    "args": GetIncidentArgs.model_json_schema(),
}
