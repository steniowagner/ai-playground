from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict
from triage_ops.domain.types import Environment
from triage_ops.tools.get_recent_deployments.schema import (
    Deployment,
)


class FindDeploymentsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    started_at: AwareDatetime
    completed_at: AwareDatetime


class DeploymentsFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    deployments: list[Deployment]
