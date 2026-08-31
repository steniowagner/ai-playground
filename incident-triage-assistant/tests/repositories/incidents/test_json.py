import json
from pathlib import Path

import pytest
from incident_triage_assistant.repositories.incidents.json import JSONIncidentRepository
from pydantic import ValidationError


def raw_incident(incident_id: str = "INC-1042") -> dict[str, object]:
    return {
        "incident_id": incident_id,
        "title": "Checkout errors",
        "environment": "production",
        "primary_service": "checkout-api",
        "alert_started_at": "2026-07-10T14:10:00Z",
        "created_at": "2026-07-10T14:12:00Z",
        "status": "investigating",
        "reported_symptoms": ["errors"],
        "alert": {
            "metric": "error_rate",
            "observed": 18.4,
            "threshold": 5.0,
            "unit": "percent",
        },
        "fixture_truth": {
            "cause": "regression",
            "expected_severity": "SEV2",
            "safe_action": "rollback",
        },
    }


def test_finds_incident_without_exposing_fixture_truth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "incidents.json"
    path.write_text(
        json.dumps({"schema_version": "1.0", "incidents": [raw_incident()]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.incidents.json.INCIDENTS_FILE", path
    )

    incident = JSONIncidentRepository().find_by_id("INC-1042")

    assert incident is not None
    assert "fixture_truth" not in incident.model_dump()


def test_returns_none_for_unknown_incident(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "incidents.json"
    path.write_text(
        json.dumps({"schema_version": "1.0", "incidents": [raw_incident()]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.incidents.json.INCIDENTS_FILE", path
    )
    assert JSONIncidentRepository().find_by_id("INC-9999") is None


def test_rejects_invalid_fixture_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "incidents.json"
    path.write_text(
        json.dumps({"schema_version": "2.0", "incidents": []}), encoding="utf-8"
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.incidents.json.INCIDENTS_FILE", path
    )
    with pytest.raises(ValidationError):
        JSONIncidentRepository().find_by_id("INC-1042")
