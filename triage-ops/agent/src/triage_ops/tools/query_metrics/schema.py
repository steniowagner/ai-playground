from datetime import timedelta

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from triage_ops.domain import Environment, ServiceMetric

DEFAULT_QUERY_WINDOW_MINUTES = 60


class QueryMetricsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    metric_names: set[ServiceMetric] = Field(..., min_length=1, max_length=5)
    start_time: AwareDatetime
    end_time: AwareDatetime

    @model_validator(mode="after")
    def validate_time_window(self) -> "QueryMetricsArgs":
        if self.end_time <= self.start_time:
            raise ValueError("'end_time' must be after 'start_time'.")

        if self.end_time - self.start_time > timedelta(
            minutes=DEFAULT_QUERY_WINDOW_MINUTES
        ):
            raise ValueError(
                f"Metric query window cannot exceed {DEFAULT_QUERY_WINDOW_MINUTES} minutes"
            )

        return self


class MetricPoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_id: str
    timestamp: AwareDatetime
    value: int | float


MetricSeries = dict[ServiceMetric, list[MetricPoint]]


class QueryMetricsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    start_time: AwareDatetime
    end_time: AwareDatetime
    requested_metric_names: set[ServiceMetric] = Field(..., min_length=1, max_length=5)
    missing_metric_names: set[ServiceMetric]
    series: MetricSeries
