from pydantic import AwareDatetime, BaseModel, ConfigDict
from triage_ops.domain.types import Environment
from triage_ops.tools.query_metrics.schema import ServiceMetric


class FindMetricsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    metric_names: set[ServiceMetric]
    start_time: AwareDatetime
    end_time: AwareDatetime
