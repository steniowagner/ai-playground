from abc import ABC, abstractmethod

from incident_triage_assistant.tools.get_recent_deployments.schema import Deployment

from .schema import FindDeploymentsArgs


class DeploymentsRepository(ABC):
    @abstractmethod
    def find(self, args: FindDeploymentsArgs) -> list[Deployment]:
        pass
