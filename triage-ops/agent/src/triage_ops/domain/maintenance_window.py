from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict

from triage_ops.domain import Environment

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
