from datetime import datetime

from incident_triage_assistant_langchain.domain.types import Environment
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    model_validator,
)


class Deployment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    deployment_id: str
    service: str
    environment: Environment
    version: str
    commit: str
    started_at: datetime
    completed_at: datetime
    status: str
    summary: str


class GetRecentDeploymentsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    started_at: AwareDatetime
    completed_at: AwareDatetime

    @model_validator(mode="after")
    def validate_time_window(self) -> "GetRecentDeploymentsArgs":
        if self.completed_at <= self.started_at:
            raise ValueError("'started_at' must be after 'completed_at'.")

        return self


class GetRecentDeploymentsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    deployments: list[Deployment]
