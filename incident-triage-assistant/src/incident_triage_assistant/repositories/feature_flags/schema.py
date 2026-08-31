from typing import Literal

from incident_triage_assistant.domain.types import Environment
from incident_triage_assistant.tools.get_feature_flags.schema import FeatureFlag
from pydantic import BaseModel, ConfigDict, Field


class FeatureFlagsFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    feature_flags: list[FeatureFlag]


class FindFeatureFlagsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    flag_name: str | None = Field(default=None, min_length=1)
