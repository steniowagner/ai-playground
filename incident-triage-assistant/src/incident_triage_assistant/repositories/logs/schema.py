from incident_triage_assistant.domain.types import Environment
from incident_triage_assistant.tools.query_logs.schema import Severity
from pydantic import AwareDatetime, BaseModel, ConfigDict


class FindLogsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    contains: str | None
    limit: int
    severity: set[Severity] | None
    start_time: AwareDatetime
    end_time: AwareDatetime
