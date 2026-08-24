import json
from pathlib import Path
from typing import Any

from .schema import GetIncidentParams, Incident, IncidentsJson, IncidentWithFixture

INCIDENTS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "incidents.json"
)


def find_incident_by_id(incident_id: str, incidents: list[Incident]) -> Incident | None:
    return next(
        (incident for incident in incidents if incident.incident_id == incident_id),
        None,
    )


def parse_incident(fixture: Any) -> Incident:
    incident_with_fixture_truth = IncidentWithFixture.model_validate(fixture)
    return Incident.model_validate(
        incident_with_fixture_truth.model_dump(exclude={"fixture_truth"})
    )


def read_incidents() -> list[Incident]:
    incidents = []

    with open(INCIDENTS_FILE, "r", encoding="utf-8") as f:
        raw_incidents_json = json.load(f)
        incidents_json = IncidentsJson.model_validate(raw_incidents_json)
        raw_incidents = incidents_json.incidents
        """Parsing again so we can properly remove "fixture_truth" from the Incident object."""
        incidents = [parse_incident(incident) for incident in raw_incidents]

    return incidents


def get_incident(raw_params: GetIncidentParams) -> Incident | None:
    params = GetIncidentParams.model_validate(raw_params)

    incidents = read_incidents()
    incident = find_incident_by_id(params.incident_id, incidents)

    return incident
