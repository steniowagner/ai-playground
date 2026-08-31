from typing import Any

from incident_triage_assistant.repositories.incidents.base import IncidentRepository
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import (
    GetIncidentArgs,
    GetIncidentResult,
)


class GetIncidentTool:
    def __init__(self, repository: IncidentRepository) -> None:
        self._repository = repository

    def __call__(self, raw_args: dict[str, Any]) -> ToolResponse[GetIncidentResult]:
        try:
            args = GetIncidentArgs.model_validate(raw_args)
        except ValidationError:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="INVALID_ARGUMENT",
                    message=f"Invalid arguments '{raw_args}'.",
                ),
            )

        incident = self._repository.find_by_id(args.incident_id)

        if not incident:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="NOT_FOUND",
                    message=f"Incident '{args.incident_id}' was not found.",
                ),
            )

        return ToolSuccessResponse(ok=True, data=GetIncidentResult(incident=incident))
