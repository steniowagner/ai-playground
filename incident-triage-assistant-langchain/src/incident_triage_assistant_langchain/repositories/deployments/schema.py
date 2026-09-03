from typing import Literal

from incident_triage_assistant_langchain.domain.types import Environment
from incident_triage_assistant_langchain.tools.get_recent_deployments.schema import (
    Deployment,
)
from pydantic import AwareDatetime, BaseModel, ConfigDict


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
