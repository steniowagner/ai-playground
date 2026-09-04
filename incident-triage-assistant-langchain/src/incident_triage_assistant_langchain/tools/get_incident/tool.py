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
        args = GetIncidentArgs(incident_id=incident_id)

        try:
            incident = self.repository.find_by_id(incident_id=args.incident_id)
        except RepositoryException as exc:
            return self._handle_error(args=args, exception=exc)

        if not incident:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="NOT_FOUND",
                    message=f"Incident '{args.incident_id}' was not found.",
                    retryable=False,
                    input=args.model_dump(mode="json"),
                    suggested_action="Verify the incident ID before trying a different lookup.",
                ),
            )

        return ToolSuccessResponse(ok=True, data=GetIncidentResult(incident=incident))

    def _handle_error(
        self, args: GetIncidentArgs, exception: RepositoryException
    ) -> ToolErrorResponse:
        logger = logging.getLogger(__name__)

        logger.exception(
            "Failed to retrieve incident.",
            extra={
                "tool_name": self.name,
                "tool_input": args.model_dump(mode="json"),
                "repository_error": type(exception).__name__,
            },
        )

        suggested_action = (
            "Retry this request once. If it fails again, stop the investigation and report the issue."
            if exception.retryable
            else "Do not retry and report the issue."
        )

        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="EXECUTION_ERROR",
                message="Failed to retrieve incident due to an internal error.",
                retryable=exception.retryable,
                input=args.model_dump(mode="json"),
                suggested_action=suggested_action,
            ),
        )
