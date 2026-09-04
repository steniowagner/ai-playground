from abc import ABC, abstractmethod

from incident_triage_assistant_langchain.tools.get_service_context.schema import Service

from .schema import FindServiceArgs


class ServicesRepository(ABC):
    @abstractmethod
    def find(self, args: FindServiceArgs) -> Service | None:
        pass
