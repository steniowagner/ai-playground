import logging

from incident_triage_assistant_langchain.domain.types import Environment
from incident_triage_assistant_langchain.repositories.exceptions import (
    RepositoryException,
)
from incident_triage_assistant_langchain.repositories.maintenance_windows.base import (
    MaintenanceWindowsRepository,
)
from incident_triage_assistant_langchain.repositories.maintenance_windows.schema import (
    FindMaintenanceWindowsArgs,
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
    GetMaintenanceWindowsArgs,
    GetMaintenanceWindowsResult,
)


class GetMaintenanceWindowsTool(BaseTool):
    name: str = "get_maintenance_windows"
    description: str = "Retrieve approved maintenance windows that overlap a requested period for one exact service and environment. Maintenance is supporting evidence, not an unconditional reason to ignore an alert or customer impact."
    parameters: type[BaseModel] = GetMaintenanceWindowsArgs
    repository: MaintenanceWindowsRepository

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
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
        }

        logger.exception(
            "Failed to retrieve maintenance windows.",
            extra=tool_input,
        )

        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="EXECUTION_ERROR",
                message="Failed to retrieve maintenance windows due an internal error.",
                retryable=True,
                input=tool_input,
                suggested_action="Retry this request once. If it fails again, continue the investigation without maintenance-window evidence.",
            ),
        )

    def _run(
        self,
        service: str,
        environment: Environment,
        start_time: AwareDatetime,
        end_time: AwareDatetime,
    ) -> ToolResponse[GetMaintenanceWindowsResult]:
        try:
            maintenance_windows = self.repository.find(
                FindMaintenanceWindowsArgs(
                    service=service,
                    environment=environment,
                    start_time=start_time,
                    end_time=end_time,
                )
            )
        except RepositoryException:
            return self._handle_error(
                service=service,
                environment=environment,
                start_time=start_time,
                end_time=end_time,
            )

        return ToolSuccessResponse(
            ok=True,
            data=GetMaintenanceWindowsResult(maintenance_windows=maintenance_windows),
        )
