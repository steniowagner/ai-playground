from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from triage_ops.domain import (
    Environment,
    IncidentSeverity,
)

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
    severity: IncidentSeverity
    reported_symptoms: list[str]
    alert: IncidentAlert


class IncidentFixtureTruth(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    cause: str
    expected_severity: IncidentSeverity
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


class IncidentsFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    incidents: list[IncidentWithFixture]
