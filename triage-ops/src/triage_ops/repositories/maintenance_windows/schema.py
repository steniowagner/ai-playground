from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict

from triage_ops.domain.types import Environment
from triage_ops.tools.get_maintenance_windows.schema import (
    MaintenanceWindow,
)


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
