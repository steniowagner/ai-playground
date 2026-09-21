from abc import ABC, abstractmethod

from triage_ops.domain import Deployment

from .schema import FindDeploymentsArgs


class DeploymentsRepository(ABC):
    @abstractmethod
    def find(self, args: FindDeploymentsArgs) -> list[Deployment]:
        pass

    @abstractmethod
    def find_all(self) -> list[Deployment]:
        pass
