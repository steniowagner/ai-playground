from datetime import datetime

import pytest
from incident_triage_assistant.tools.get_incident.schema import (
    GetIncidentArgs,
    Incident,
    IncidentAlert,
)
from incident_triage_assistant.repositories.incidents.schema import IncidentWithFixture
from pydantic import ValidationError


def valid_incident() -> dict[str, object]:
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
    }


def test_get_incident_args_accepts_valid_incident_id() -> None:
    args = GetIncidentArgs.model_validate({"incident_id": "INC-1042"})
    assert args.incident_id == "INC-1042"


@pytest.mark.parametrize("incident_id", ["INC-42", "inc-1042", "INC-ABCD", "1042", ""])
def test_get_incident_args_rejects_invalid_id(incident_id: str) -> None:
    with pytest.raises(ValidationError):
        GetIncidentArgs.model_validate({"incident_id": incident_id})


def test_get_incident_args_rejects_extra_properties() -> None:
    with pytest.raises(ValidationError):
        GetIncidentArgs.model_validate(
            {"incident_id": "INC-1042", "environment": "production"}
        )


def test_incident_parses_nested_alert_and_timestamps() -> None:
    incident = Incident.model_validate(valid_incident())
    assert isinstance(incident.alert, IncidentAlert)
    assert isinstance(incident.alert_started_at, datetime)
    assert incident.alert.observed == 18.4


def test_public_incident_rejects_fixture_truth() -> None:
    raw = valid_incident()
    raw["fixture_truth"] = {
        "cause": "secret evaluator answer",
        "expected_severity": "SEV2",
        "safe_action": "rollback_deployment",
    }
    with pytest.raises(ValidationError):
        Incident.model_validate(raw)


def test_internal_fixture_requires_fixture_truth() -> None:
    with pytest.raises(ValidationError):
        IncidentWithFixture.model_validate(valid_incident())
