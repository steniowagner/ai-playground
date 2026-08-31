from abc import ABC, abstractmethod

from incident_triage_assistant.tools.query_logs.schema import Log

from .schema import FindLogsArgs


class LogsRepository(ABC):
    @abstractmethod
    def find(args: FindLogsArgs) -> list[Log]:
        pass
