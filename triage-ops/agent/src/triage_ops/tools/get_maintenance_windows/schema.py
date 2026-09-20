from datetime import timedelta

from pydantic import AwareDatetime, BaseModel, ConfigDict, model_validator

from triage_ops.domain import Environment, MaintenanceWindow

MAX_QUERY_WINDOW_HOURS = 24


class GetMaintenanceWindowsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    start_time: AwareDatetime
    end_time: AwareDatetime

    @model_validator(mode="after")
    def validate_time_window(self) -> "GetMaintenanceWindowsArgs":
        if self.end_time <= self.start_time:
            raise ValueError("'end_time' must be after 'start_time'.")

        if self.end_time - self.start_time > timedelta(hours=MAX_QUERY_WINDOW_HOURS):
            raise ValueError(
                f"Maintenance query window cannot exceed {MAX_QUERY_WINDOW_HOURS} hours."
            )

        return self


class GetMaintenanceWindowsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    maintenance_windows: list[MaintenanceWindow]
