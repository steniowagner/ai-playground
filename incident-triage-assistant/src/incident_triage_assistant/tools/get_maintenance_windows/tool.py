import json
from pathlib import Path
from typing import Any

from incident_triage_assistant.tools.tool_response import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import (
    GetMaintenanceWindowsArgs,
    GetMaintenanceWindowsResult,
    MaintenanceWindow,
    MaintenanceWindowsFixture,
)

MAINTENANCE_WINDOWS_FILE = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "fixtures"
    / "maintenance_windows.json"
)


def read_maintenance_windows() -> list[MaintenanceWindow]:
    with open(MAINTENANCE_WINDOWS_FILE, "r", encoding="utf-8") as f:
        raw_maintenance_windows_json = json.load(f)
        maintenance_windows_fixture = MaintenanceWindowsFixture.model_validate(
            raw_maintenance_windows_json
        )
        return maintenance_windows_fixture.maintenance_windows


def find_maintenance_windows(
    args: GetMaintenanceWindowsArgs,
) -> list[MaintenanceWindow]:
    maintenance_windows = read_maintenance_windows()

    matching_windows = [
        maintenance_window
        for maintenance_window in maintenance_windows
        if args.service in maintenance_window.services
        and maintenance_window.environment == args.environment
        and maintenance_window.start_time < args.end_time
        and args.start_time < maintenance_window.end_time
    ]

    return sorted(matching_windows, key=lambda window: window.start_time)


def get_maintenance_windows(
    raw_args: dict[str, Any],
) -> ToolResponse[GetMaintenanceWindowsResult]:
    try:
        args = GetMaintenanceWindowsArgs.model_validate(raw_args)
    except ValidationError:
        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="INVALID_ARGUMENT", message=f"Invalid arguments '{raw_args}'"
            ),
        )

    maintenance_windows = find_maintenance_windows(args)

    return ToolSuccessResponse(
        ok=True,
        data=GetMaintenanceWindowsResult(maintenance_windows=maintenance_windows),
    )
