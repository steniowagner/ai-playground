from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

Environment = Literal["production", "staging"]

ServiceMetric = Literal[
    "error_rate",
    "p95_latency_ms",
    "request_rate",
    "cpu_percent",
    "queue_depth",
]


class QueryTimeWindow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    started_at: datetime
    completed_at: datetime

    @field_validator("completed_at")
    @classmethod
    def ensure_started_at_before_completed_at(
        cls, v: datetime, info: ValidationInfo
    ) -> datetime:
        started_at = info.data.get("started_at")

        if started_at and v <= started_at:
            raise ValueError("'started_at' must be before 'completed_at'")

        return v
