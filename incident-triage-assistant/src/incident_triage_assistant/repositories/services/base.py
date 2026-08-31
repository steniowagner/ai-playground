from abc import ABC, abstractmethod

from incident_triage_assistant.domain.types import Environment
from incident_triage_assistant.tools.get_service_context.schema import Service


class ServicesRepository(ABC):
    @abstractmethod
    def find(self, service: str, environment: Environment) -> Service | None:
        pass
