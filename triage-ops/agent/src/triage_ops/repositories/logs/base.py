from abc import ABC, abstractmethod

from triage_ops.domain import Log

from .schema import FindLogsArgs


class LogsRepository(ABC):
    @abstractmethod
    def find(self, args: FindLogsArgs) -> list[Log]:
        pass

    @abstractmethod
    def find_all(self) -> list[Log]:
        pass
