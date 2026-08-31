from incident_triage_assistant.domain.types import Environment
from incident_triage_assistant.tools.query_metrics.schema import ServiceMetric
from pydantic import AwareDatetime, BaseModel, ConfigDict


class FindMetricsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    metric_names: set[ServiceMetric]
    start_time: AwareDatetime
    end_time: AwareDatetime
