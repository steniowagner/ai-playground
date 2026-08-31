from abc import ABC, abstractmethod


class RunbooksRepository(ABC):
    @abstractmethod
    def find_by_id(self, runbook_id: str) -> str | None:
        pass
