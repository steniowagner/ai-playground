from abc import ABC, abstractmethod

from triage_ops.domain import MaintenanceWindow

from .schema import FindMaintenanceWindowsArgs


class MaintenanceWindowsRepository(ABC):
    @abstractmethod
    def find(self, args: FindMaintenanceWindowsArgs) -> list[MaintenanceWindow]:
        pass

    @abstractmethod
    def find_all(self) -> list[MaintenanceWindow]:
        pass
