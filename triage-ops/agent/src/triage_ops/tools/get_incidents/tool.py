import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel

from triage_ops.repositories import (
    RepositoryException,
)
from triage_ops.repositories.incidents import (
    IncidentRepository,
)
from triage_ops.tools import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)

from ..schema import ToolNames
from .schema import GetIncidentsArgs, GetIncidentsResult


class GetIncidentsTool(BaseTool):
    name: str = ToolNames.GET_INCIDENTS
    description: str = "List all registered incidents and their recorded details. Use this to discover available incidents when no exact incident ID is known or when comparing incidents."
    args_schema: type[BaseModel] = GetIncidentsArgs
    repository: IncidentRepository

    def _run(self) -> ToolResponse[GetIncidentsResult]:
        try:
            incidents = self.repository.find()
        except RepositoryException as exc:
            return self._handle_error(exception=exc)

        return ToolSuccessResponse(
            ok=True, data=GetIncidentsResult(incidents=incidents)
        )

    def _handle_error(self, exception: RepositoryException) -> ToolErrorResponse:
        logger = logging.getLogger(__name__)

        logger.exception(
            "Failed to retrieve incidents.",
            extra={
                "tool_name": self.name,
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
                message="Failed to retrieve incidents due to an internal error.",
                retryable=exception.retryable,
                input={},
                suggested_action=suggested_action,
            ),
        )
