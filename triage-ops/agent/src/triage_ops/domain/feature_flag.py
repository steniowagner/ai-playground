from pydantic import AwareDatetime, BaseModel, ConfigDict

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
