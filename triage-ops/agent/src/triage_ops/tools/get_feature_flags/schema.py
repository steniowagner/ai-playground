from pydantic import BaseModel, ConfigDict, Field

from triage_ops.domain import Environment, FeatureFlag


class GetFeatureFlagsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    flag_name: str | None = Field(default=None, min_length=1)


class GetFeatureFlagsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    feature_flags: list[FeatureFlag]
