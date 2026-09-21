from abc import ABC, abstractmethod

from triage_ops.repositories.incidents import Incident


class IncidentRepository(ABC):
    @abstractmethod
    def find_by_id(self, incident_id: str) -> Incident | None:
        pass

    @abstractmethod
    def find_all(self) -> list[Incident]:
        pass
