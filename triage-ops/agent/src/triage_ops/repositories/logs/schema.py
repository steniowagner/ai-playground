from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict

from triage_ops.domain import Environment

LogSeverity = Literal["ERROR", "WARN", "INFO"]


class Log(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    log_id: str
    timestamp: AwareDatetime
    service: str
    environment: Environment
    severity: LogSeverity
    trace_id: str | None = None
    message: str
    attributes: dict[str, Any]


class FindLogsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    contains: str | None
    limit: int
    severity: set[LogSeverity] | None
    start_time: AwareDatetime
    end_time: AwareDatetime
