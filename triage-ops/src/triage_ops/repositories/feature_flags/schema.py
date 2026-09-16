from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from triage_ops.domain.types import Environment
from triage_ops.tools.get_feature_flags.schema import (
    FeatureFlag,
)


class FeatureFlagsFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    feature_flags: list[FeatureFlag]


class FindFeatureFlagsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    flag_name: str | None = Field(default=None, min_length=1)
