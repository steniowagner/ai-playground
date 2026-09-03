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
        try:
            deployments = self.repository.find(
                FindDeploymentsArgs(
                    service=service,
                    environment=environment,
                    started_at=started_at,
                    completed_at=completed_at,
                )
            )
        except RepositoryException:
            return self._handle_error(
                service=service,
                environment=environment,
                started_at=started_at,
                completed_at=completed_at,
            )

        return ToolSuccessResponse(
            ok=True, data=GetRecentDeploymentsResult(deployments=deployments)
        )

    def _handle_error(
        self,
        service: str,
        environment: Environment,
        start_time: AwareDatetime,
        end_time: AwareDatetime,
    ) -> ToolErrorResponse:
        logger = logging.getLogger(__name__)

        tool_input = {
            "service": service,
            "environment": environment,
            "start_time": start_time,
            "end_time": end_time,
        }

        logger.exception(
            "Failed to retrieve recent deployments.",
            extra=tool_input,
        )

        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="EXECUTION_ERROR",
                message="Failed to retrieve recent deployments due an internal error.",
                retryable=True,
                input=tool_input,
                suggested_action="Retry this request once. If it fails again, continue the investigation without recent-deployments evidence and let the user know about the error.",
            ),
        )
