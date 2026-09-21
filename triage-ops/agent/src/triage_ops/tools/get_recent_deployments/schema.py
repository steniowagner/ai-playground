from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    model_validator,
)

from triage_ops.domain import Deployment, Environment


class GetRecentDeploymentsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    started_at: AwareDatetime
    completed_at: AwareDatetime

    @model_validator(mode="after")
    def validate_time_window(self) -> "GetRecentDeploymentsArgs":
        if self.completed_at <= self.started_at:
            raise ValueError("'completed_at' must be after 'started_at'.")

        return self


class GetRecentDeploymentsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    deployments: list[Deployment]
