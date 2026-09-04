from abc import ABC, abstractmethod

from .schema import FindRunbookByIdArgs


class RunbooksRepository(ABC):
    @abstractmethod
    def find_by_id(self, args: FindRunbookByIdArgs) -> str | None:
        pass
