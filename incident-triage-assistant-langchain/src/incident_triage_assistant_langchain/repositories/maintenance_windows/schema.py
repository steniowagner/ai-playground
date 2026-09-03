from typing import Literal

from incident_triage_assistant_langchain.domain.types import Environment
from incident_triage_assistant_langchain.tools.get_maintenance_windows.schema import (
    MaintenanceWindow,
)
from pydantic import AwareDatetime, BaseModel, ConfigDict


class MaintenanceWindowsFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    maintenance_windows: list[MaintenanceWindow]


class FindMaintenanceWindowsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
    start_time: AwareDatetime
    end_time: AwareDatetime
