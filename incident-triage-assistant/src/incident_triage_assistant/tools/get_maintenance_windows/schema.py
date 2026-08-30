from datetime import timedelta
from typing import Literal

from incident_triage_assistant.domain.types import Environment
from pydantic import AwareDatetime, BaseModel, ConfigDict, model_validator

MAX_QUERY_WINDOW_HOURS = 24
MaintenanceStatus = Literal["scheduled", "in_progress", "completed", "cancelled"]


class MaintenanceWindow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    maintenance_id: str
    title: str
    services: list[str]
    environment: Environment
    start_time: AwareDatetime
    end_time: AwareDatetime
    expected_effects: list[str]
    approved_by: str
    status: MaintenanceStatus


class MaintenanceWindowsFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    maintenance_windows: list[MaintenanceWindow]


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
