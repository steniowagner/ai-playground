from typing import Any

from incident_triage_assistant.repositories.services.base import ServicesRepository
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import (
    GetServiceContextArgs,
    GetServiceContextResult,
)


class GetServiceContextTool:
    def __init__(self, repository: ServicesRepository) -> None:
        self._repository = repository

    def __call__(
        self, raw_args: dict[str, Any]
    ) -> ToolResponse[GetServiceContextResult]:
        try:
            args = GetServiceContextArgs.model_validate(raw_args)
        except ValidationError:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="INVALID_ARGUMENT", message=f"Invalid arguments '{raw_args}'"
                ),
            )

        service = self._repository.find(args.service, args.environment)

        if not service:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="NOT_FOUND",
                    message=f"Service '{args.service}' running in '{args.environment}' not found.",
                ),
            )

        return ToolSuccessResponse(
            ok=True, data=GetServiceContextResult(service=service)
        )
