from abc import ABC, abstractmethod

from incident_triage_assistant.tools.get_incident.schema import Incident


class IncidentRepository(ABC):
    @abstractmethod
    def find_by_id(self, incident_id: str) -> Incident | None:
        pass
