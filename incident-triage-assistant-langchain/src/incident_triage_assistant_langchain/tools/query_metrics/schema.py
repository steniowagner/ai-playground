from datetime import datetime, timedelta
from typing import Literal

from incident_triage_assistant_langchain.domain.types import (
    Environment,
)
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

DEFAULT_QUERY_WINDOW_MINUTES = 60

ServiceMetric = Literal[
    "error_rate",
    "p95_latency_ms",
    "request_rate",
    "cpu_percent",
    "queue_depth",
]


class MetricValues(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    error_rate: float | None = None
    p95_latency_ms: int | None = None
    request_rate: float | None = None
    queue_depth: int | None = None
    cpu_percent: float | None = None


class Metric(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_id: str
    timestamp: datetime
    service: str
    environment: Environment
    values: MetricValues


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
    timestamp: datetime
    value: int | float


MetricSeries = dict[ServiceMetric, list[MetricPoint]]


class QueryMetricsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    start_time: datetime
    end_time: datetime
    requested_metric_names: set[ServiceMetric] = Field(..., min_length=1, max_length=5)
    missing_metric_names: set[ServiceMetric]
    series: MetricSeries
