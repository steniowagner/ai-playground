import json
from pathlib import Path
from typing import Any

from incident_triage_assistant.tools.get_incident.schema import (
    Incident,
)

from .base import IncidentRepository
from .schema import IncidentsFixture, IncidentWithFixture

INCIDENTS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "incidents.json"
)


class JSONIncidentRepository(IncidentRepository):
    def _parse_incident(self, fixture: Any) -> Incident:
        incident_with_fixture_truth = IncidentWithFixture.model_validate(fixture)
        return Incident.model_validate(
            incident_with_fixture_truth.model_dump(exclude={"fixture_truth"})
        )

    def _read_incidents(self) -> list[Incident]:
        incidents = []

        with open(INCIDENTS_FILE, "r", encoding="utf-8") as f:
            raw_incidents_json = json.load(f)
            incidents_json = IncidentsFixture.model_validate(raw_incidents_json)
            raw_incidents = incidents_json.incidents
            """Parsing again so we can properly remove "fixture_truth" from the Incident object."""
            incidents = [self._parse_incident(incident) for incident in raw_incidents]

        return incidents

    def find_by_id(self, incident_id: str) -> Incident | None:
        incidents = self._read_incidents()

        return next(
            (incident for incident in incidents if incident.incident_id == incident_id),
            None,
        )
