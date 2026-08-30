from incident_triage_assistant.tools.types import Tool

from .schema import GetServiceContextArgs

GET_SERVICE_CONTEXT_TOOL = Tool(
    name="get_service_context",
    description="Retrieve operational context for one exact service and environment, including ownership, on-call information, dependencies, SLOs, and associated runbook IDs. Use this after identifying the incident's affected service.",
    parameters=GetServiceContextArgs.model_json_schema(),
)
