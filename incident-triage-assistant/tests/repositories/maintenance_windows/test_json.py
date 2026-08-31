import json
from pathlib import Path

import pytest
from incident_triage_assistant.repositories.maintenance_windows.json import (
    JSONMaintenanceWindowsRepository,
)
from incident_triage_assistant.repositories.maintenance_windows.schema import (
    FindMaintenanceWindowsArgs,
)
from pydantic import ValidationError


def window(
    identifier: str, start: str, end: str, service: str = "catalog-api"
) -> dict[str, object]:
    return {
        "maintenance_id": identifier,
        "title": "Maintenance",
        "services": [service],
        "environment": "production",
        "start_time": start,
        "end_time": end,
        "expected_effects": ["latency"],
        "approved_by": "ops",
        "status": "scheduled",
    }


def test_returns_overlapping_windows_sorted_by_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "windows.json"
    items = [
        window("later", "2026-08-20T10:20:00Z", "2026-08-20T10:40:00Z"),
        window("earlier", "2026-08-20T09:50:00Z", "2026-08-20T10:10:00Z"),
        window("touches-boundary", "2026-08-20T09:00:00Z", "2026-08-20T10:00:00Z"),
        window("other", "2026-08-20T10:05:00Z", "2026-08-20T10:10:00Z", "checkout-api"),
    ]
    path.write_text(
        json.dumps({"schema_version": "1.0", "maintenance_windows": items}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.maintenance_windows.json.MAINTENANCE_WINDOWS_FILE",
        path,
    )
    args = FindMaintenanceWindowsArgs(
        service="catalog-api",
        environment="production",
        start_time="2026-08-20T10:00:00Z",
        end_time="2026-08-20T10:30:00Z",
    )
    assert [
        item.maintenance_id for item in JSONMaintenanceWindowsRepository().find(args)
    ] == ["earlier", "later"]


def test_rejects_invalid_fixture_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "windows.json"
    path.write_text(
        json.dumps({"schema_version": "1.0", "maintenance_windows": [], "extra": True}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "incident_triage_assistant.repositories.maintenance_windows.json.MAINTENANCE_WINDOWS_FILE",
        path,
    )
    args = FindMaintenanceWindowsArgs(
        service="catalog-api",
        environment="production",
        start_time="2026-08-20T10:00:00Z",
        end_time="2026-08-20T10:30:00Z",
    )
    with pytest.raises(ValidationError):
        JSONMaintenanceWindowsRepository().find(args)
