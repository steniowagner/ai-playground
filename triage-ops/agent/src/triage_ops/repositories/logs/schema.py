from pydantic import AwareDatetime, BaseModel, ConfigDict

from triage_ops.domain import Environment
from triage_ops.tools.query_logs import Severity


class FindLogsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    contains: str | None
    limit: int
    severity: set[Severity] | None
    start_time: AwareDatetime
    end_time: AwareDatetime
