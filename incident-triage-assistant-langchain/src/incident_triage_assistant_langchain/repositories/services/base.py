from abc import ABC, abstractmethod

from incident_triage_assistant_langchain.domain.types import Environment
from incident_triage_assistant_langchain.tools.get_service_context.schema import Service


class ServicesRepository(ABC):
    @abstractmethod
    def find(self, service: str, environment: Environment) -> Service | None:
        pass
