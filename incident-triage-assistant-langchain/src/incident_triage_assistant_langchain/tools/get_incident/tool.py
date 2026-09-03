import logging

from incident_triage_assistant_langchain.repositories.exceptions import (
    RepositoryException,
)
from incident_triage_assistant_langchain.repositories.incidents.base import (
    IncidentRepository,
)
from incident_triage_assistant_langchain.tools.schema import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
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

    def _run(self, incident_id: str) -> ToolResponse[GetIncidentResult]:
        try:
            incident = self.repository.find_by_id(incident_id)
        except RepositoryException:
            return self._handle_error(incident_id)

        if not incident:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="NOT_FOUND",
                    message=f"Incident '{incident_id}' was not found.",
                ),
            )

        return ToolSuccessResponse(ok=True, data=GetIncidentResult(incident=incident))

    def _handle_error(self, incident_id: str) -> ToolErrorResponse:
        logger = logging.getLogger(__name__)

        tool_input = {
            "incident_id": incident_id,
        }

        logger.exception(
            "Failed to retrieve incident.",
            extra=tool_input,
        )

        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="EXECUTION_ERROR",
                message="Failed to retrieve incident due an internal error.",
                retryable=True,
                input=tool_input,
                suggested_action="Retry this request once. If it fails again, stop the investigation and let the user knows that it was due this error.",
            ),
        )
