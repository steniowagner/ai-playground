from abc import ABC, abstractmethod

from triage_ops.tools.get_recent_deployments.schema import (
    Deployment,
)

from .schema import FindDeploymentsArgs


class DeploymentsRepository(ABC):
    @abstractmethod
    def find(self, args: FindDeploymentsArgs) -> list[Deployment]:
        pass
