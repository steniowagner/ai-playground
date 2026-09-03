import logging

from incident_triage_assistant_langchain.domain.types import Environment
from incident_triage_assistant_langchain.repositories.exceptions import (
    RepositoryException,
)
from incident_triage_assistant_langchain.repositories.services.base import (
    ServicesRepository,
)
from incident_triage_assistant_langchain.tools.schema import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from .schema import (
    GetServiceContextArgs,
    GetServiceContextResult,
)


class GetServiceContextTool(BaseTool):
    name: str = "get_service_context"
    description: str = "Retrieve operational context for one exact service and environment, including ownership, on-call information, dependencies, SLOs, and associated runbook IDs. Use this after identifying the incident's affected service."
    args_schema: type[BaseModel] = GetServiceContextArgs
    repository: ServicesRepository

    def _run(
        self, service: str, environment: Environment
    ) -> ToolResponse[GetServiceContextResult]:
        try:
            service = self.repository.find(service=service, environment=environment)
        except RepositoryException:
            return self._handle_error(service=service, environment=environment)

        if not service:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="NOT_FOUND",
                    message=f"Service '{service}' running in '{environment}' not found.",
                ),
            )

        return ToolSuccessResponse(
            ok=True, data=GetServiceContextResult(service=service)
        )

    def _handle_error(
        self, service: str, environment: Environment
    ) -> ToolErrorResponse:
        logger = logging.getLogger(__name__)

        tool_input = {"service": service, "environment": environment}

        logger.exception(
            "Failed to retrieve service.",
            extra=tool_input,
        )

        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="EXECUTION_ERROR",
                message="Failed to retrieve service due an internal error.",
                retryable=True,
                input=tool_input,
                suggested_action="Retry this request once. If it fails again, stop the investigation and let the user knows that it was due this error.",
            ),
        )
