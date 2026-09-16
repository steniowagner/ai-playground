from abc import ABC, abstractmethod

from triage_ops.tools.get_incident import Incident


class IncidentRepository(ABC):
    @abstractmethod
    def find_by_id(self, incident_id: str) -> Incident | None:
        pass
