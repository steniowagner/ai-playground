import json
from pathlib import Path
from typing import Any

from incident_triage_assistant_langchain.tools.get_incident.schema import Incident
from pydantic import ValidationError

from ..exceptions import RepositoryDataError, RepositoryUnavailable
from .base import IncidentRepository
from .schema import IncidentsFixture

INCIDENTS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "incidents.json"
)


class JSONIncidentRepository(IncidentRepository):
    def _parse_fixture(self, incidents_json: Any) -> IncidentsFixture:
        try:
            return IncidentsFixture.model_validate(incidents_json)
        except ValidationError as exc:
            raise RepositoryDataError("Incidents repository data is invalid.") from exc

    def _read_incidents(self) -> list[Incident]:
        try:
            with open(INCIDENTS_FILE, "r", encoding="utf-8") as f:
                incidents_json = json.load(f)
        except UnicodeDecodeError as exc:
            raise RepositoryDataError(
                "Incidents repository contains invalid text data."
            ) from exc
        except json.JSONDecodeError as exc:
            raise RepositoryDataError(
                "Incidents repository contains invalid JSON."
            ) from exc
        except OSError as exc:
            raise RepositoryUnavailable("Incidents repository is unavailable.") from exc

        fixture = self._parse_fixture(incidents_json)

        return [
            Incident.model_validate(incident.model_dump(exclude={"fixture_truth"}))
            for incident in fixture.incidents
        ]

    def find_by_id(self, incident_id: str) -> Incident | None:
        return next(
            (
                incident
                for incident in self._read_incidents()
                if incident.incident_id == incident_id
            ),
            None,
        )
