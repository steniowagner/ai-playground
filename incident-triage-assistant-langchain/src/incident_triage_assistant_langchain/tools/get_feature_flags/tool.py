from incident_triage_assistant_langchain.domain.types import Environment
from incident_triage_assistant_langchain.repositories.feature_flags.base import (
    FeatureFlagsRepository,
)
from incident_triage_assistant_langchain.repositories.feature_flags.schema import (
    FindFeatureFlagsArgs,
)
from incident_triage_assistant_langchain.tools.schema import (
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
        self, service: str, environment: Environment, flag_name: str | None
    ) -> ToolResponse[GetFeatureFlagsResult]:
        feature_flags = self.repository.find(
            FindFeatureFlagsArgs(
                service=service,
                environment=environment,
                flag_name=flag_name,
            )
        )

        return ToolSuccessResponse(
            ok=True, data=GetFeatureFlagsResult(feature_flags=feature_flags)
        )
