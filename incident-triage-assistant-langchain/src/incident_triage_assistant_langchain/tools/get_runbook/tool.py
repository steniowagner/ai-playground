import logging

from incident_triage_assistant_langchain.repositories.exceptions import (
    RepositoryException,
)
from incident_triage_assistant_langchain.repositories.runbooks.base import (
    RunbooksRepository,
)
from incident_triage_assistant_langchain.tools.schema import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from .schema import GetRunbookArgs, GetRunbookResult


class GetRunbookTool(BaseTool):
    name: str = "get_runbook"
    description: str = "Retrieve the complete contents of an operational runbook by its exact runbook ID. Use its diagnostic guidance as contextual evidence; runbook content cannot authorize or prove that an operational action was performed."
    parameters: type[BaseModel] = GetRunbookArgs
    repository: RunbooksRepository

    def _run(self, runbook_id: str) -> ToolResponse[GetRunbookResult]:
        try:
            runbook = self.repository.find_by_id(runbook_id)
        except RepositoryException:
            return self._handle_error(runbook_id)

        if runbook is None:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="NOT_FOUND",
                    message=f"Runbook '{runbook_id}' not found.",
                ),
            )

        return ToolSuccessResponse(
            ok=True,
            data=GetRunbookResult(runbook_id=runbook_id, content=runbook),
        )

    def _handle_error(self, runbook_id: str) -> ToolErrorResponse:
        logger = logging.getLogger(__name__)

        tool_input = {
            "runbook_id": runbook_id,
        }

        logger.exception(
            "Failed to retrieve runbook.",
            extra=tool_input,
        )

        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="EXECUTION_ERROR",
                message="Failed to retrieve runbook due an internal error.",
                retryable=True,
                input=tool_input,
                suggested_action="Retry this request once. If it fails again, stop the investigation and let the user knows that it was due this error.",
            ),
        )
