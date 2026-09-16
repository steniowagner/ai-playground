from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from triage_ops.domain.types import (
    Environment,
)


class RestartServiceArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str = Field(
        min_length=1,
        description=(
            "Service to restart, copied exactly from a successful tool result."
        ),
    )

    environment: Environment = Field(
        description=(
            "Environment in which to restart, copied exactly from a successful "
            "tool result."
        )
    )

    strategy: Literal["rolling", "immediate"] = Field(
        description=(
            "'rolling' replaces instances gradually and preserves availability. "
            "'immediate' restarts all instances at once and causes a short "
            "outage. Choose 'immediate' only when evidence shows a rolling "
            "restart cannot clear the condition."
        )
    )
