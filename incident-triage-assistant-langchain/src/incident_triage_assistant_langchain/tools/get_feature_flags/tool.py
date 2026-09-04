import logging

from incident_triage_assistant_langchain.domain.types import Environment
from incident_triage_assistant_langchain.repositories.exceptions import (
    RepositoryException,
)
from incident_triage_assistant_langchain.repositories.feature_flags.base import (
    FeatureFlagsRepository,
)
from incident_triage_assistant_langchain.repositories.feature_flags.schema import (
    FindFeatureFlagsArgs,
)
from incident_triage_assistant_langchain.tools.schema import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from .schema import (
    GetFeatureFlagsArgs,
    GetFeatureFlagsResult,
)


class GetFeatureFlagsTool(BaseTool):
    name: str = "get_feature_flags"
    description: str = "Retrieve feature flags for one exact service and environment, optionally filtered by an exact flag name. Use flag state and change metadata as investigation evidence, but do not treat timing alone as proof of causation or claim that this read-only tool changed a flag."
    args_schema: type[BaseModel] = GetFeatureFlagsArgs
    repository: FeatureFlagsRepository

    def _run(
        self, service: str, environment: Environment, flag_name: str | None = None
    ) -> ToolResponse[GetFeatureFlagsResult]:
        args = GetFeatureFlagsArgs(
            service=service, environment=environment, flag_name=flag_name
        )

        try:
            feature_flags = self.repository.find(
                FindFeatureFlagsArgs(**args.model_dump())
            )
        except RepositoryException as exc:
            return self._handle_error(args=args, exception=exc)

        return ToolSuccessResponse(
            ok=True, data=GetFeatureFlagsResult(feature_flags=feature_flags)
        )

    def _handle_error(
        self, args: GetFeatureFlagsArgs, exception: RepositoryException
    ) -> ToolErrorResponse:
        logger = logging.getLogger(__name__)

        logger.exception(
            "Failed to retrieve feature-flags.",
            extra={
                "tool_name": self.name,
                "tool_input": args.model_dump(mode="json"),
                "repository_error": type(exception).__name__,
            },
        )

        suggested_action = (
            "Retry this request once. If it fails again, continue without feature-flag evidence and report the limitation."
            if exception.retryable
            else "Do not retry. Continue without feature-flag evidence and report the limitation."
        )

        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="EXECUTION_ERROR",
                message="Failed to retrieve feature-flag due to an internal error.",
                retryable=exception.retryable,
                input=args.model_dump(mode="json"),
                suggested_action=suggested_action,
            ),
        )
