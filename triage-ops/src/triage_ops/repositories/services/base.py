from abc import ABC, abstractmethod

from triage_ops.tools.get_service_context import Service

from .schema import FindServiceArgs


class ServicesRepository(ABC):
    @abstractmethod
    def find(self, args: FindServiceArgs) -> Service | None:
        pass
