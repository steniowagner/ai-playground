from typing import Any

from incident_triage_assistant.repositories.feature_flags.base import (
    FeatureFlagsRepository,
)
from incident_triage_assistant.repositories.feature_flags.schema import (
    FindFeatureFlagsArgs,
)
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import (
    GetFeatureFlagsArgs,
    GetFeatureFlagsResult,
)


class GetFeatureFlagsTool:
    def __init__(self, repository: FeatureFlagsRepository) -> None:
        self._repository = repository

    def __call__(self, raw_args: dict[str, Any]) -> ToolResponse[GetFeatureFlagsResult]:
        try:
            args = GetFeatureFlagsArgs.model_validate(raw_args)
        except ValidationError:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="INVALID_ARGUMENT", message=f"Invalid arguments '{raw_args}'."
                ),
            )

        feature_flags = self._repository.find(
            FindFeatureFlagsArgs(
                service=args.service,
                environment=args.environment,
                flag_name=args.flag_name,
            )
        )

        return ToolSuccessResponse(
            ok=True, data=GetFeatureFlagsResult(feature_flags=feature_flags)
        )
