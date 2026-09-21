from datetime import timedelta

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from triage_ops.domain import Environment, Log, LogSeverity

DEFAULT_QUERY_WINDOW_MINUTES = 60


class QueryLogsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    contains: str | None = Field(
        default=None,
        description=(
            "Optional case-sensitive message substring. Omit when no message filter is needed."
        ),
    )
    limit: int = Field(default=50, ge=1, le=50)
    severity: set[LogSeverity] | None = Field(
        default=None,
        min_length=1,
        max_length=3,
        description=(
            "Optional severity allow-list. "
            "Omit to include ERROR, WARN, and INFO logs. "
            "Never send the string 'None'."
        ),
    )
    start_time: AwareDatetime
    end_time: AwareDatetime

    @model_validator(mode="after")
    def validate_time_window(self) -> "QueryLogsArgs":
        if self.end_time <= self.start_time:
            raise ValueError("'end_time' must be after 'start_time'.")

        if self.end_time - self.start_time > timedelta(
            minutes=DEFAULT_QUERY_WINDOW_MINUTES
        ):
            raise ValueError(
                f"Log query window cannot exceed {DEFAULT_QUERY_WINDOW_MINUTES} minutes"
            )

        return self


class QueryLogsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    logs: list[Log]
