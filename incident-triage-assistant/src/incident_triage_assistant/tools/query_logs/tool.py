from typing import Any

from incident_triage_assistant.repositories.logs.base import LogsRepository
from incident_triage_assistant.repositories.logs.schema import FindLogsArgs
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import QueryLogsArgs, QueryLogsResult


class QueryLogsTool:
    def __init__(self, repository: LogsRepository) -> None:
        self._repository = repository

    def __call__(self, raw_args: dict[str, Any]) -> ToolResponse[QueryLogsResult]:
        try:
            args = QueryLogsArgs.model_validate(raw_args)
        except ValidationError:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="INVALID_ARGUMENT", message=f"Invalid arguments '{raw_args}'"
                ),
            )

        logs = self._repository.find(
            FindLogsArgs(
                service=args.service,
                environment=args.environment,
                contains=args.contains,
                limit=args.limit,
                severity=args.severity,
                start_time=args.start_time,
                end_time=args.end_time,
            )
        )

        return ToolSuccessResponse(ok=True, data=QueryLogsResult(logs=logs))
