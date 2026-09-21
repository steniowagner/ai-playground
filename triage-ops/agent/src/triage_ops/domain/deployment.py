from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
)

from triage_ops.domain import Environment


class Deployment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    deployment_id: str
    service: str
    environment: Environment
    version: str
    commit: str
    started_at: AwareDatetime
    completed_at: AwareDatetime
    status: str
    summary: str
