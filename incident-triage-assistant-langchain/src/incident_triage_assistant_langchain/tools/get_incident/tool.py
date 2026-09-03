from incident_triage_assistant_langchain.repositories.incidents.base import (
    IncidentRepository,
)
from incident_triage_assistant_langchain.tools.schema import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolSuccessResponse,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from .schema import GetIncidentArgs, GetIncidentResult


class GetIncidentTool(BaseTool):
    name: str = "get_incident"
    description: str = "Retrieve the recorded details of one incident by its exact incident ID, including the affected service, environment, alert, status, timestamps, and reported symptoms. Use this as the starting point when investigating a known incident."
    args_schema: type[BaseModel] = GetIncidentArgs
    repository: IncidentRepository

    def _run(self, incident_id: str) -> ToolSuccessResponse:
        incident = self.repository.find_by_id(incident_id)

        if not incident:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="NOT_FOUND",
                    message=f"Incident '{incident_id}' was not found.",
                ),
            )

        return ToolSuccessResponse(ok=True, data=GetIncidentResult(incident=incident))
