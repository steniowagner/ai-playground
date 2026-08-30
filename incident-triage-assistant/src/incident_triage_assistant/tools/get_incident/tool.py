import json
from pathlib import Path
from typing import Any

from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import (
    GetIncidentArgs,
    GetIncidentResult,
    Incident,
    IncidentsFixture,
    IncidentWithFixture,
)

INCIDENTS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "incidents.json"
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
        incidents_json = IncidentsFixture.model_validate(raw_incidents_json)
        raw_incidents = incidents_json.incidents
        """Parsing again so we can properly remove "fixture_truth" from the Incident object."""
        incidents = [parse_incident(incident) for incident in raw_incidents]

    return incidents


def find_incident(incident_id: str) -> Incident | None:
    incidents = read_incidents()
    return next(
        (incident for incident in incidents if incident.incident_id == incident_id),
        None,
    )


def get_incident(raw_args: dict[str, Any]) -> ToolResponse[GetIncidentResult]:
    try:
        args = GetIncidentArgs.model_validate(raw_args)
    except ValidationError:
        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="INVALID_ARGUMENT",
                message=f"Invalid arguments '{raw_args}'.",
            ),
        )

    incident = find_incident(args.incident_id)

    if not incident:
        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="NOT_FOUND",
                message=f"Incident '{args.incident_id}' was not found.",
            ),
        )

    return ToolSuccessResponse(ok=True, data=GetIncidentResult(incident=incident))
