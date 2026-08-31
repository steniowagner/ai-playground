import json
from pathlib import Path

from incident_triage_assistant.tools.get_maintenance_windows.schema import (
    MaintenanceWindow,
)

from .base import MaintenanceWindowsRepository
from .schema import FindMaintenanceWindowsArgs, MaintenanceWindowsFixture

MAINTENANCE_WINDOWS_FILE = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "fixtures"
    / "maintenance_windows.json"
)


class JSONMaintenanceWindowsRepository(MaintenanceWindowsRepository):
    def _read_maintenance_windows(self) -> list[MaintenanceWindow]:
        with open(MAINTENANCE_WINDOWS_FILE, "r", encoding="utf-8") as f:
            raw_maintenance_windows_json = json.load(f)
            maintenance_windows_fixture = MaintenanceWindowsFixture.model_validate(
                raw_maintenance_windows_json
            )
            return maintenance_windows_fixture.maintenance_windows

    def find(self, args: FindMaintenanceWindowsArgs) -> list[MaintenanceWindow]:
        maintenance_windows = self._read_maintenance_windows()

        matching_windows = [
            maintenance_window
            for maintenance_window in maintenance_windows
            if args.service in maintenance_window.services
            and maintenance_window.environment == args.environment
            and maintenance_window.start_time < args.end_time
            and args.start_time < maintenance_window.end_time
        ]

        return sorted(matching_windows, key=lambda window: window.start_time)
