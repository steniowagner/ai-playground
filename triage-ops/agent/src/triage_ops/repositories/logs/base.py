from abc import ABC, abstractmethod

from triage_ops.tools.query_logs import Log

from .schema import FindLogsArgs


class LogsRepository(ABC):
    @abstractmethod
    def find(self, args: FindLogsArgs) -> list[Log]:
        pass
