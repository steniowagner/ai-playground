from abc import ABC, abstractmethod

from incident_triage_assistant_langchain.tools.query_logs.schema import Log

from .schema import FindLogsArgs


class LogsRepository(ABC):
    @abstractmethod
    def find(self, args: FindLogsArgs) -> list[Log]:
        pass
