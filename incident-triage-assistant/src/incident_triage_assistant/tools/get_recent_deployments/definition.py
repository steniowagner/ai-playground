from incident_triage_assistant.tools.types import Tool

from .schema import GetRecentDeploymentsArgs

GET_RECENT_DEPLOYMENTS_TOOL = Tool(
    name="get_recent_deployments",
    description="Retrieve deployments for one exact service and environment within the requested time window. Use this to identify changes near an incident, but treat timing as correlation rather than proof of causation.",
    parameters=GetRecentDeploymentsArgs.model_json_schema(),
)
