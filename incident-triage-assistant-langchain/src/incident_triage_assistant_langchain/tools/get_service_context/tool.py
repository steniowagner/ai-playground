import logging

from incident_triage_assistant_langchain.domain.types import Environment
from incident_triage_assistant_langchain.repositories.exceptions import (
    RepositoryException,
)
from incident_triage_assistant_langchain.repositories.services.base import (
    ServicesRepository,
)
from incident_triage_assistant_langchain.repositories.services.schema import (
    FindServiceArgs,
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
        args = GetServiceContextArgs(service=service, environment=environment)

        try:
            service_context = self.repository.find(FindServiceArgs(**args.model_dump()))
        except RepositoryException as exc:
            return self._handle_error(args=args, exception=exc)

        if service_context is None:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="NOT_FOUND",
                    message=f"Service '{args.service}' running in '{args.environment}' was not found.",
                    retryable=False,
                    input=args.model_dump(mode="json"),
                    suggested_action="Verify the service name and environment before retrying.",
                ),
            )

        return ToolSuccessResponse(
            ok=True, data=GetServiceContextResult(service=service_context)
        )

    def _handle_error(
        self, args: GetServiceContextArgs, exception: RepositoryException
    ) -> ToolErrorResponse:
        logger = logging.getLogger(__name__)

        logger.exception(
            "Failed to retrieve service.",
            extra={
                "tool_name": self.name,
                "tool_input": args.model_dump(mode="json"),
                "repository_error": type(exception).__name__,
            },
        )

        suggested_action = (
            "Retry this request once. If it fails again, continue without service evidence and report the limitation."
            if exception.retryable
            else "Do not retry. Continue without service-context evidence and report the limitation."
        )

        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="EXECUTION_ERROR",
                message="Failed to retrieve service due to an internal error.",
                retryable=exception.retryable,
                input=args.model_dump(mode="json"),
                suggested_action=suggested_action,
            ),
        )
