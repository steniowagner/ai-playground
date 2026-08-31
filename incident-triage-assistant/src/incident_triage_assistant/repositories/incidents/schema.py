from typing import Literal

from incident_triage_assistant.tools.get_incident.schema import Incident
from pydantic import BaseModel, ConfigDict


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


class IncidentsFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    incidents: list[IncidentWithFixture]
