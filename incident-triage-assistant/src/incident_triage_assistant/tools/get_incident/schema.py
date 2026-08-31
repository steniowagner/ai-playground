from datetime import datetime
from typing import Literal

from incident_triage_assistant.domain.types import Environment
from pydantic import BaseModel, ConfigDict, Field

IncidentStatus = Literal["investigating", "monitoring", "resolved"]


class IncidentAlert(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric: str
    observed: float
    threshold: float
    unit: str


class Incident(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: str
    title: str
    environment: Environment
    primary_service: str
    alert_started_at: datetime
    created_at: datetime
    status: IncidentStatus
    reported_symptoms: list[str]
    alert: IncidentAlert


class GetIncidentArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: str = Field(
        pattern=r"^INC-[0-9]{4}$", description="Incident-id to be used in the search."
    )


class GetIncidentResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident: Incident
