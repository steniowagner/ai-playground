from incident_triage_assistant.domain.types import Tool

from .schema import GetRecentDeploymentsArgs

GET_RECENT_DEPLOYMENTS_TOOL: Tool = {
    "name": "get_recent_deployments",
    "description": "Determine whether a deployment occurred near the beginning of an incident.",
    "parameters": GetRecentDeploymentsArgs.model_json_schema(),
}
