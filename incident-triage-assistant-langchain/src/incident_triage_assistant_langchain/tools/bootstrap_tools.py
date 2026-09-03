from incident_triage_assistant_langchain.repositories.incidents.json import (
    JSONIncidentRepository,
)
from langchain_core.tools import BaseTool

from .get_incident.tool import GetIncidentTool


def bootstrap_tools() -> list[BaseTool]:
    json_incidents_repository = JSONIncidentRepository()

    tools = [GetIncidentTool(repository=json_incidents_repository)]

    return tools
