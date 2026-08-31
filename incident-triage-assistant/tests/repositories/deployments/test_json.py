import json
from pathlib import Path

import pytest
from incident_triage_assistant.repositories.deployments.json import (
    JSONDeploymentsRepository,
)
from incident_triage_assistant.repositories.deployments.schema import (
    FindDeploymentsArgs,
)


def deployment(
    identifier: str, completed_at: str, service: str = "checkout-api"
) -> dict[str, object]:
    return {
        "deployment_id": identifier,
        "service": service,
        "environment": "production",
        "version": "1.0",
        "commit": "abc123",
        "started_at": "2026-08-20T10:00:00Z",
        "completed_at": completed_at,
        "status": "succeeded",
        "summary": "Update",
    }


def test_filters_by_context_and_time_then_sorts_newest_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "deployments.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "deployments": [
                    deployment("older", "2026-08-20T10:05:00Z"),
                    deployment("newer", "2026-08-20T10:20:00Z"),
                    deployment("other", "2026-08-20T10:15:00Z", "catalog-api"),
                    deployment("outside", "2026-08-20T11:30:00Z"),
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.deployments.json.DEPLOYMENTS_FILE", path
    )
    args = FindDeploymentsArgs(
        service="checkout-api",
        environment="production",
        started_at="2026-08-20T10:00:00Z",
        completed_at="2026-08-20T11:00:00Z",
    )
    result = JSONDeploymentsRepository().find(args)
    assert [item.deployment_id for item in result] == ["newer", "older"]


def test_returns_empty_list_when_nothing_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "deployments.json"
    path.write_text(
        json.dumps({"schema_version": "1.0", "deployments": []}), encoding="utf-8"
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.deployments.json.DEPLOYMENTS_FILE", path
    )
    args = FindDeploymentsArgs(
        service="checkout-api",
        environment="production",
        started_at="2026-08-20T10:00:00Z",
        completed_at="2026-08-20T11:00:00Z",
    )
    assert JSONDeploymentsRepository().find(args) == []
