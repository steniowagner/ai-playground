from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from triage_ops.domain.types import (
    Environment,
)


class DisableFeatureFlagServiceArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str = Field(
        min_length=1,
        description=(
            "Service the flag applies to, copied exactly from a successful tool result."
        ),
    )

    environment: Environment = Field(
        description=(
            "Environment in which the flag should be disabled, copied exactly "
            "from the feature-flag record."
        )
    )

    flag_key: str = Field(
        min_length=1,
        description=(
            "Key of the flag to disable, copied exactly from get_feature_flags. "
            "Never construct or guess this value."
        ),
    )
