from incident_triage_assistant.tools.get_tools import Tool

from .schema import GetServiceContextArgs

GET_SERVICE_CONTEXT_TOOL: Tool = {
    "name": "get_service_context",
    "description": "Retrieve operational information about a service after the agent discovers the affected service from an incident.",
    "args": GetServiceContextArgs.model_json_schema(),
}
