from typing import Any

from incident_triage_assistant.repositories.runbooks.base import RunbooksRepository
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import GetRunbookArgs, GetRunbookResult


class GetRunbookTool:
    def __init__(self, repository: RunbooksRepository) -> None:
        self._repository = repository

    def __call__(self, raw_args: dict[str, Any]) -> ToolResponse[GetRunbookResult]:
        try:
            args = GetRunbookArgs.model_validate(raw_args)
        except ValidationError:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="INVALID_ARGUMENT", message=f"Invalid arguments '{raw_args}'."
                ),
            )

        runbook = self._repository.find_by_id(args.runbook_id)

        if runbook is None:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="NOT_FOUND",
                    message=f"Runbook '{args.runbook_id}' not found.",
                ),
            )

        return ToolSuccessResponse(
            ok=True,
            data=GetRunbookResult(runbook_id=args.runbook_id, content=runbook),
        )
