from datetime import datetime

from incident_triage_assistant.domain.types import Environment, IncidentStatus
from pydantic import BaseModel, ConfigDict, Field


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


class IncidentFixtureTruth(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    cause: str
    expected_severity: str
    safe_action: str


class IncidentWithFixture(Incident):
    """
    By default, incidents recorded at incidents.json have the descriptions for their solutions on the "fixture_truth" field, which means that
    we should not return it to LLM through the tools.

    To solve that, we'll have this intermediate schema to validate the incidents from incidents.json.
    After parsed, we'll remove the "fixture_truth" and return a standard Incident schema.

    "fixture_truth" are used for the evaluation only.
    """

    fixture_truth: IncidentFixtureTruth


class IncidentsJson(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str
    incidents: list[IncidentWithFixture]


class GetIncidentArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: str = Field(
        pattern=r"^INC-[0-9]{4}$", description="Incident-id to be used in the search."
    )
