from incident_triage_assistant_langchain.domain.types import Environment
from incident_triage_assistant_langchain.tools.query_metrics.schema import ServiceMetric
from pydantic import AwareDatetime, BaseModel, ConfigDict


class FindMetricsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    metric_names: set[ServiceMetric]
    start_time: AwareDatetime
    end_time: AwareDatetime
