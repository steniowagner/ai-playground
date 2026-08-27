from incident_triage_assistant.domain.types import Tool

from .get_incident.definition import GET_INCIDENT_TOOL
from .get_recent_deployments.definition import GET_RECENT_DEPLOYMENTS_TOOL
from .get_service_context.definition import GET_SERVICE_CONTEXT_TOOL

tools = [GET_SERVICE_CONTEXT_TOOL, GET_INCIDENT_TOOL, GET_RECENT_DEPLOYMENTS_TOOL]


def get_tools() -> list[Tool]:
    return [Tool.model_validate(tool) for tool in tools]
