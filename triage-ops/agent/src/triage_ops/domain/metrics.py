from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict

from .types import (
    Environment,
)

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
    timestamp: AwareDatetime
    service: str
    environment: Environment
    values: MetricValues
