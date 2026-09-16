from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from triage_ops.domain import Environment


class FeatureFlag(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    flag: str
    service: str
    environment: Environment
    enabled: bool
    owner_team: str
    changed_at: AwareDatetime
    changed_by_deployment: str


class GetFeatureFlagsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    flag_name: str | None = Field(default=None, min_length=1)


class GetFeatureFlagsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    feature_flags: list[FeatureFlag]


class FeatureFlagsFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    feature_flags: list[FeatureFlag]
