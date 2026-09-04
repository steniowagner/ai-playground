import json
from pathlib import Path
from typing import Any

from incident_triage_assistant_langchain.tools.get_maintenance_windows.schema import (
    MaintenanceWindow,
)
from pydantic import ValidationError

from ..exceptions import RepositoryDataError, RepositoryUnavailable
from .base import MaintenanceWindowsRepository
from .schema import FindMaintenanceWindowsArgs, MaintenanceWindowsFixture

MAINTENANCE_WINDOWS_FILE = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "fixtures"
    / "maintenance_windows.json"
)


class JSONMaintenanceWindowsRepository(MaintenanceWindowsRepository):
    def _parse_fixture(self, fixture_json: Any) -> MaintenanceWindowsFixture:
        try:
            return MaintenanceWindowsFixture.model_validate(fixture_json)
        except ValidationError as exc:
            raise RepositoryDataError(
                "Maintenance-windows repository data is invalid."
            ) from exc

    def _read_maintenance_windows(self) -> list[MaintenanceWindow]:
        try:
            with open(MAINTENANCE_WINDOWS_FILE, "r", encoding="utf-8") as f:
                maintenance_windows_json = json.load(f)
        except json.JSONDecodeError as exc:
            raise RepositoryDataError(
                "Maintenance-windows repository contains invalid JSON."
            ) from exc
        except UnicodeDecodeError as exc:
            raise RepositoryDataError(
                "Maintenance-windows repository contains invalid text data."
            ) from exc
        except OSError as exc:
            raise RepositoryUnavailable(
                "Maintenance-windows repository is unavailable."
            ) from exc

        fixture = self._parse_fixture(maintenance_windows_json)
        return fixture.maintenance_windows

    def find(self, args: FindMaintenanceWindowsArgs) -> list[MaintenanceWindow]:
        maintenance_windows = self._read_maintenance_windows()

        matching_windows = [
            maintenance_window
            for maintenance_window in maintenance_windows
            if args.service in maintenance_window.services
            and maintenance_window.environment == args.environment
            and maintenance_window.status != "cancelled"
            and maintenance_window.start_time < args.end_time
            and args.start_time < maintenance_window.end_time
        ]

        return sorted(matching_windows, key=lambda window: window.start_time)
