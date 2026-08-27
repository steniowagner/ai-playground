from datetime import datetime

from incident_triage_assistant.domain.types import Environment, QueryTimeWindow
from pydantic import (
    BaseModel,
    ConfigDict,
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


class GetRecentDeploymentsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    query_window: QueryTimeWindow | None = None
