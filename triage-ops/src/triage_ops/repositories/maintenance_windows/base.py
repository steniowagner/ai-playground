from abc import ABC, abstractmethod

from triage_ops.tools.get_maintenance_windows.schema import (
    MaintenanceWindow,
)

from .schema import FindMaintenanceWindowsArgs


class MaintenanceWindowsRepository(ABC):
    @abstractmethod
    def find(self, args: FindMaintenanceWindowsArgs) -> list[MaintenanceWindow]:
        pass
