from unittest.mock import Mock

import pytest
from incident_triage_assistant.repositories.maintenance_windows.base import (
    MaintenanceWindowsRepository,
)
from incident_triage_assistant.tools.get_maintenance_windows.schema import (
    MaintenanceWindow,
)
from incident_triage_assistant.tools.get_maintenance_windows.tool import (
    GetMaintenanceWindowsTool,
)
from incident_triage_assistant.tools.types import ToolErrorResponse, ToolSuccessResponse


def window() -> MaintenanceWindow:
    return MaintenanceWindow.model_validate(
        {
            "maintenance_id": "MW-1",
            "title": "Database maintenance",
            "services": ["catalog-api"],
            "environment": "production",
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T10:30:00Z",
            "expected_effects": ["latency"],
            "approved_by": "ops",
            "status": "scheduled",
        }
    )


def test_returns_repository_results_and_forwards_query() -> None:
    repository = Mock(spec=MaintenanceWindowsRepository)
    repository.find.return_value = [window()]
    response = GetMaintenanceWindowsTool(repository)(
        {
            "service": "catalog-api",
            "environment": "production",
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T11:00:00Z",
        }
    )
    assert isinstance(response, ToolSuccessResponse)
    assert response.data.maintenance_windows == [window()]
    args = repository.find.call_args.args[0]
    assert (args.service, args.environment) == ("catalog-api", "production")


def test_returns_empty_success_for_no_matches() -> None:
    repository = Mock(spec=MaintenanceWindowsRepository)
    repository.find.return_value = []
    response = GetMaintenanceWindowsTool(repository)(
        {
            "service": "catalog-api",
            "environment": "production",
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T11:00:00Z",
        }
    )
    assert isinstance(response, ToolSuccessResponse)
    assert response.data.maintenance_windows == []


@pytest.mark.parametrize(
    "args",
    [
        {},
        {
            "service": "catalog-api",
            "environment": "production",
            "start_time": "2026-08-20T11:00:00Z",
            "end_time": "2026-08-20T10:00:00Z",
        },
        {
            "service": "catalog-api",
            "environment": "unknown",
            "start_time": "2026-08-20T10:00:00Z",
            "end_time": "2026-08-20T11:00:00Z",
        },
    ],
)
def test_rejects_invalid_arguments_without_querying_repository(
    args: dict[str, object],
) -> None:
    repository = Mock(spec=MaintenanceWindowsRepository)
    response = GetMaintenanceWindowsTool(repository)(args)
    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"
    repository.find.assert_not_called()
