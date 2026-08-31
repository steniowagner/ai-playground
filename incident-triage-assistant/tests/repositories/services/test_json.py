import json
from pathlib import Path

import pytest
from incident_triage_assistant.repositories.services.json import JSONServicesRepository
from pydantic import ValidationError


def service(name: str, environments: list[str]) -> dict[str, object]:
    return {
        "service": name,
        "display_name": name,
        "description": "Service",
        "tier": 1,
        "owner_team": "platform",
        "on_call": "platform-oncall",
        "environments": environments,
        "dependencies": [],
        "runbook_ids": [],
        "slo": {},
    }


def write_fixture(
    path: Path, services: list[dict[str, object]], schema_version: str = "1.0"
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "company": "Example",
                "services": services,
                "external_dependencies": [],
            }
        ),
        encoding="utf-8",
    )


def test_finds_service_available_in_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "services.json"
    write_fixture(path, [service("catalog-api", ["staging", "production"])])
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.services.json.SERVICES_FILE", path
    )
    result = JSONServicesRepository().find("catalog-api", "production")
    assert result is not None
    assert result.service == "catalog-api"


def test_returns_none_for_wrong_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "services.json"
    write_fixture(path, [service("catalog-api", ["staging"])])
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.services.json.SERVICES_FILE", path
    )
    assert JSONServicesRepository().find("catalog-api", "production") is None


def test_rejects_invalid_schema_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "services.json"
    write_fixture(path, [], "2.0")
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.services.json.SERVICES_FILE", path
    )
    with pytest.raises(ValidationError):
        JSONServicesRepository().find("catalog-api", "production")
