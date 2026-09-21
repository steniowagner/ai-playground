from abc import ABC, abstractmethod

from triage_ops.domain import Service

from .schema import FindServiceArgs


class ServicesRepository(ABC):
    @abstractmethod
    def find(self, args: FindServiceArgs) -> Service | None:
        pass

    @abstractmethod
    def find_all(self) -> list[Service]:
        pass
