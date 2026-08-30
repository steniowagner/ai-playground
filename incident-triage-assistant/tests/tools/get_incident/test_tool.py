import json
from pathlib import Path

import pytest
from incident_triage_assistant.tools.get_incident.schema import Incident
from incident_triage_assistant.tools.get_incident.tool import (
    find_incident,
    get_incident,
    parse_incident,
    read_incidents,
)
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError


def raw_fixture() -> dict[str, object]:
    return {
        "incident_id": "INC-1042",
        "title": "Production checkout error-rate spike",
        "environment": "production",
        "primary_service": "checkout-api",
        "alert_started_at": "2026-07-10T14:10:00Z",
        "created_at": "2026-07-10T14:12:00Z",
        "status": "investigating",
        "reported_symptoms": ["checkout errors increased"],
        "alert": {
            "metric": "error_rate",
            "observed": 18.4,
            "threshold": 5.0,
            "unit": "percent",
        },
        "fixture_truth": {
            "cause": "regression",
            "expected_severity": "SEV2",
            "safe_action": "rollback_deployment",
        },
    }


def test_parse_incident_removes_fixture_truth() -> None:
    incident = parse_incident(raw_fixture())
    assert isinstance(incident, Incident)
    assert incident.incident_id == "INC-1042"
    assert "fixture_truth" not in incident.model_dump()


def test_parse_incident_rejects_invalid_fixture() -> None:
    with pytest.raises(ValidationError):
        parse_incident({"incident_id": "INC-1042"})


def test_find_incident_returns_match() -> None:
    result = find_incident("INC-1044")
    assert result is not None
    assert result.primary_service == "notification-worker"


def test_find_incident_returns_none_when_missing() -> None:
    assert find_incident("INC-9999") is None


def test_read_incidents_returns_all_safe_fixture_records() -> None:
    incidents = read_incidents()
    assert len(incidents) == 8
    assert {item.incident_id for item in incidents} == {
        "INC-1042",
        "INC-1043",
        "INC-1044",
        "INC-1045",
        "INC-1046",
        "INC-1047",
        "INC-1048",
        "INC-1049",
    }
    assert all("fixture_truth" not in item.model_dump() for item in incidents)


def test_read_incidents_rejects_invalid_top_level_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "incidents.json"
    path.write_text(
        json.dumps({"schema_version": "1.0", "incidents": [], "unexpected": True}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "incident_triage_assistant.tools.get_incident.tool.INCIDENTS_FILE", path
    )
    with pytest.raises(ValidationError):
        read_incidents()


def test_get_incident_accepts_raw_dictionary() -> None:
    response = get_incident({"incident_id": "INC-1043"})

    assert isinstance(response, ToolSuccessResponse)
    incident = response.data.incident
    assert isinstance(incident, Incident)
    assert incident.incident_id == "INC-1043"
    assert incident.primary_service == "payment-adapter"
    assert response.error is None


def test_get_incident_returns_not_found_for_unknown_valid_id() -> None:
    response = get_incident({"incident_id": "INC-9999"})

    assert isinstance(response, ToolErrorResponse)
    assert response.data is None
    assert response.error.code == "NOT_FOUND"
    assert "INC-9999" in response.error.message


@pytest.mark.parametrize(
    "args",
    [{"incident_id": "invalid"}, {"incident_id": "INC-1043", "extra": True}, {}],
)
def test_get_incident_returns_invalid_argument_for_invalid_args(
    args: dict[str, object],
) -> None:
    response = get_incident(args)

    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"
