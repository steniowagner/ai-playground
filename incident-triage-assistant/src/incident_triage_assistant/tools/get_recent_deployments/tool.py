from typing import Any

from incident_triage_assistant.repositories.deployments.base import (
    DeploymentsRepository,
)
from incident_triage_assistant.repositories.deployments.schema import (
    FindDeploymentsArgs,
)
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import (
    GetRecentDeploymentsArgs,
    GetRecentDeploymentsResult,
)


class GetRecentDeploymentsTool:
    def __init__(self, repository: DeploymentsRepository) -> None:
        self._repository = repository

    def __call__(
        self, raw_args: dict[str, Any]
    ) -> ToolResponse[GetRecentDeploymentsResult]:
        try:
            args = GetRecentDeploymentsArgs.model_validate(raw_args)
        except ValidationError:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="INVALID_ARGUMENT", message=f"Invalid arguments '{raw_args}'"
                ),
            )

        deployments = self._repository.find(
            FindDeploymentsArgs(
                service=args.service,
                environment=args.environment,
                started_at=args.started_at,
                completed_at=args.completed_at,
            )
        )

        return ToolSuccessResponse(
            ok=True, data=GetRecentDeploymentsResult(deployments=deployments)
        )
