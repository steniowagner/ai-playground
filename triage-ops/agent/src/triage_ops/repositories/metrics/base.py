from abc import ABC, abstractmethod

from triage_ops.domain import Metric

from .schema import FindMetricsArgs


class MetricsRepository(ABC):
    @abstractmethod
    def find(self, args: FindMetricsArgs) -> list[Metric]:
        pass

    @abstractmethod
    def find_all(self) -> list[Metric]:
        pass
