from incident_triage_assistant_langchain.domain.types import Environment
from incident_triage_assistant_langchain.tools.query_logs.schema import Severity
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
