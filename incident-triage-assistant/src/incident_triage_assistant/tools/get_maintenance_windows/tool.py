from typing import Any

from incident_triage_assistant.repositories.maintenance_windows.base import (
    MaintenanceWindowsRepository,
)
from incident_triage_assistant.repositories.maintenance_windows.schema import (
    FindMaintenanceWindowsArgs,
)
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import (
    GetMaintenanceWindowsArgs,
    GetMaintenanceWindowsResult,
)


class GetMaintenanceWindowsTool:
    def __init__(self, repository: MaintenanceWindowsRepository) -> None:
        self._repository = repository

    def __call__(
        self,
        raw_args: dict[str, Any],
    ) -> ToolResponse[GetMaintenanceWindowsResult]:
        try:
            args = GetMaintenanceWindowsArgs.model_validate(raw_args)
        except ValidationError:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="INVALID_ARGUMENT", message=f"Invalid arguments '{raw_args}'"
                ),
            )

        maintenance_windows = self._repository.find(
            FindMaintenanceWindowsArgs(
                service=args.service,
                environment=args.environment,
                start_time=args.start_time,
                end_time=args.end_time,
            )
        )

        return ToolSuccessResponse(
            ok=True,
            data=GetMaintenanceWindowsResult(maintenance_windows=maintenance_windows),
        )
