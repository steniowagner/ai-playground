from datetime import datetime

from incident_triage_assistant.domain.types import Environment
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationInfo,
    field_validator,
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


class DeploymentsJson(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    deployments: list[Deployment]


class QueryWindow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    started_at: datetime
    completed_at: datetime

    @field_validator("completed_at")
    @classmethod
    def ensure_started_at_before_completed_at(
        cls, v: datetime, info: ValidationInfo
    ) -> datetime:
        started_at = info.data.get("started_at")

        if started_at and v <= started_at:
            raise ValueError("'started_at' must be before 'completed_at'")

        return v


class GetRecentDeploymentsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    query_window: QueryWindow | None = None
