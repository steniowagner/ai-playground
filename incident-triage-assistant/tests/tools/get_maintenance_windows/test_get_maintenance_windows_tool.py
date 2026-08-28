import json
from pathlib import Path
from typing import Any

import pytest
from incident_triage_assistant.tools.get_maintenance_windows.tool import (
    get_maintenance_windows,
    read_maintenance_windows,
)
from incident_triage_assistant.tools.tool_response import (
    ToolErrorResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError


def write_maintenance_windows_file(
    path: Path,
    maintenance_windows: list[dict[str, Any]],
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "maintenance_windows": maintenance_windows,
            }
        ),
        encoding="utf-8",
    )


def test_returns_overlapping_windows_for_service_sorted_by_start_time(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    maintenance_file = tmp_path / "maintenance_windows.json"
    write_maintenance_windows_file(
        maintenance_file,
        [
            {
                "maintenance_id": "MW-LATER",
                "title": "Later catalog maintenance",
                "services": ["catalog-api", "catalog-postgres"],
                "environment": "production",
                "start_time": "2026-08-20T10:15:00Z",
                "end_time": "2026-08-20T10:45:00Z",
                "expected_effects": ["increased latency"],
                "approved_by": "alice.ops",
                "status": "scheduled",
            },
            {
                "maintenance_id": "MW-OTHER-SERVICE",
                "title": "Checkout maintenance",
                "services": ["checkout-api"],
                "environment": "production",
                "start_time": "2026-08-20T10:05:00Z",
                "end_time": "2026-08-20T10:25:00Z",
                "expected_effects": ["brief errors"],
                "approved_by": "bob.ops",
                "status": "in_progress",
            },
            {
                "maintenance_id": "MW-EARLIER",
                "title": "Earlier catalog maintenance",
                "services": ["catalog-api"],
                "environment": "production",
                "start_time": "2026-08-20T09:50:00Z",
                "end_time": "2026-08-20T10:10:00Z",
                "expected_effects": ["reduced throughput"],
                "approved_by": "alice.ops",
                "status": "completed",
            },
            {
                "maintenance_id": "MW-NO-OVERLAP",
                "title": "Old catalog maintenance",
                "services": ["catalog-api"],
                "environment": "production",
                "start_time": "2026-08-20T08:00:00Z",
                "end_time": "2026-08-20T09:00:00Z",
                "expected_effects": ["increased latency"],
                "approved_by": "alice.ops",
                "status": "completed",
            },
        ],
    )
    monkeypatch.setattr(
        "incident_triage_assistant.tools.get_maintenance_windows.tool.MAINTENANCE_WINDOWS_FILE",
        maintenance_file,
    )

    response = get_maintenance_windows(
        {
            "service": "catalog-api",
            "environment": "production",
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
        }
    )

    assert isinstance(response, ToolSuccessResponse)
    assert [window.maintenance_id for window in response.data.maintenance_windows] == [
        "MW-EARLIER",
        "MW-LATER",
    ]


def test_returns_empty_success_when_no_windows_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    maintenance_file = tmp_path / "maintenance_windows.json"
    write_maintenance_windows_file(maintenance_file, [])
    monkeypatch.setattr(
        "incident_triage_assistant.tools.get_maintenance_windows.tool.MAINTENANCE_WINDOWS_FILE",
        maintenance_file,
    )

    response = get_maintenance_windows(
        {
            "service": "catalog-api",
            "environment": "production",
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
        }
    )

    assert isinstance(response, ToolSuccessResponse)
    assert response.data.maintenance_windows == []


def test_rejects_invalid_fixture_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    maintenance_file = tmp_path / "maintenance_windows.json"
    maintenance_file.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "maintenance_windows": [],
                "unexpected": True,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "incident_triage_assistant.tools.get_maintenance_windows.tool.MAINTENANCE_WINDOWS_FILE",
        maintenance_file,
    )

    with pytest.raises(ValidationError):
        read_maintenance_windows()


@pytest.mark.parametrize(
    "invalid_args",
    [
        {
            "service": "catalog-api",
            "environment": "production",
            "start_time": "2026-08-20T10:30:00Z",
            "end_time": "2026-08-20T10:00:00Z",
        },
        {
            "service": "catalog-api",
            "environment": "production",
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-21T10:01:00Z",
        },
        {
            "service": "catalog-api",
            "environment": "production",
            "start_time": "2026-08-20T10:00:00",
            "end_time": "2026-08-20T10:30:00",
        },
        {
            "service": "catalog-api",
            "environment": "unknown",
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
        },
        {
            "service": "catalog-api",
            "environment": "production",
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
            "extra": True,
        },
        {},
    ],
)
def test_returns_invalid_argument_for_invalid_input(
    invalid_args: dict[str, Any],
) -> None:
    response = get_maintenance_windows(invalid_args)

    assert isinstance(response, ToolErrorResponse)
    assert response.ok is False
    assert response.error.code == "INVALID_ARGUMENT"
    assert response.error.message.strip()
