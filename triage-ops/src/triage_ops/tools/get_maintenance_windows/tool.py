import logging

from langchain_core.tools import BaseTool
from pydantic import AwareDatetime, BaseModel

from triage_ops.domain import Environment
from triage_ops.repositories import (
    RepositoryException,
)
from triage_ops.repositories.maintenance_windows import (
    FindMaintenanceWindowsArgs,
    MaintenanceWindowsRepository,
)
from triage_ops.tools import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)

from ..schema import ToolNames
from .schema import (
    GetMaintenanceWindowsArgs,
    GetMaintenanceWindowsResult,
)


class GetMaintenanceWindowsTool(BaseTool):
    name: str = ToolNames.GET_MAINTENANCE_WINDOWS
    description: str = "Retrieve approved maintenance windows that overlap a requested period for one exact service and environment. Maintenance is supporting evidence, not an unconditional reason to ignore an alert or customer impact."
    args_schema: type[BaseModel] = GetMaintenanceWindowsArgs
    repository: MaintenanceWindowsRepository

    def _run(
        self,
        service: str,
        environment: Environment,
        start_time: AwareDatetime,
        end_time: AwareDatetime,
    ) -> ToolResponse[GetMaintenanceWindowsResult]:
        args = GetMaintenanceWindowsArgs(
            service=service,
            environment=environment,
            start_time=start_time,
            end_time=end_time,
        )

        try:
            maintenance_windows = self.repository.find(
                FindMaintenanceWindowsArgs(**args.model_dump())
            )
        except RepositoryException as exc:
            return self._handle_error(args=args, exception=exc)

        return ToolSuccessResponse(
            ok=True,
            data=GetMaintenanceWindowsResult(maintenance_windows=maintenance_windows),
        )

    def _handle_error(
        self, args: GetMaintenanceWindowsArgs, exception: RepositoryException
    ) -> ToolErrorResponse:
        logger = logging.getLogger(__name__)

        logger.exception(
            "Failed to retrieve maintenance windows.",
            extra={
                "tool_name": self.name,
                "tool_input": args.model_dump(mode="json"),
                "repository_error": type(exception).__name__,
            },
        )

        suggested_action = (
            "Retry this request once. If it fails again, continue without maintenance-window evidence and report the limitation."
            if exception.retryable
            else "Do not retry. Continue without maintenance-window evidence and report the limitation."
        )

        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="EXECUTION_ERROR",
                message="Failed to retrieve maintenance windows due to an internal error.",
                retryable=exception.retryable,
                input=args.model_dump(mode="json"),
                suggested_action=suggested_action,
            ),
        )
