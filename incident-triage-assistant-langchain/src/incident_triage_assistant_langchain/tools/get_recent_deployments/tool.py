import logging

from incident_triage_assistant_langchain.domain.types import Environment
from incident_triage_assistant_langchain.repositories.deployments.base import (
    DeploymentsRepository,
)
from incident_triage_assistant_langchain.repositories.deployments.schema import (
    FindDeploymentsArgs,
)
from incident_triage_assistant_langchain.repositories.exceptions import (
    RepositoryException,
)
from incident_triage_assistant_langchain.tools.schema import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from langchain_core.tools import BaseTool
from pydantic import AwareDatetime, BaseModel

from .schema import (
    GetRecentDeploymentsArgs,
    GetRecentDeploymentsResult,
)


class GetRecentDeploymentsTool(BaseTool):
    name: str = "get_recent_deployments"
    description: str = "Retrieve deployments for one exact service and environment within the requested time window. Use this to identify changes near an incident, but treat timing as correlation rather than proof of causation."
    args_schema: type[BaseModel] = GetRecentDeploymentsArgs
    repository: DeploymentsRepository

    def _run(
        self,
        service: str,
        environment: Environment,
        started_at: AwareDatetime,
        completed_at: AwareDatetime,
    ) -> ToolResponse[GetRecentDeploymentsResult]:
        args = GetRecentDeploymentsArgs(
            service=service,
            environment=environment,
            started_at=started_at,
            completed_at=completed_at,
        )

        try:
            deployments = self.repository.find(FindDeploymentsArgs(**args.model_dump()))
        except RepositoryException as exc:
            return self._handle_error(args=args, exception=exc)

        return ToolSuccessResponse(
            ok=True, data=GetRecentDeploymentsResult(deployments=deployments)
        )

    def _handle_error(
        self, args: GetRecentDeploymentsArgs, exception: RepositoryException
    ) -> ToolErrorResponse:
        logger = logging.getLogger(__name__)

        logger.exception(
            "Failed to retrieve recent deployments.",
            extra={
                "tool_name": self.name,
                "tool_input": args.model_dump(mode="json"),
                "repository_error": type(exception).__name__,
            },
        )

        suggested_action = (
            "Retry this request once. If it fails again, continue without recent-deployment evidence and report the limitation."
            if exception.retryable
            else "Do not retry. Continue without recent-deployment evidence and report the limitation."
        )

        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="EXECUTION_ERROR",
                message="Failed to retrieve recent deployments due to an internal error.",
                retryable=exception.retryable,
                input=args.model_dump(mode="json"),
                suggested_action=suggested_action,
            ),
        )
