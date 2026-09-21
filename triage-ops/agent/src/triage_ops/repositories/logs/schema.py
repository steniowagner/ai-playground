from pydantic import AwareDatetime, BaseModel, ConfigDict

from triage_ops.domain import Environment, LogSeverity


class FindLogsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    contains: str | None
    limit: int
    severity: set[LogSeverity] | None
    start_time: AwareDatetime
    end_time: AwareDatetime
