from abc import ABC, abstractmethod

from triage_ops.tools.query_metrics.schema import Metric

from .schema import FindMetricsArgs


class MetricsRepository(ABC):
    @abstractmethod
    def find(self, args: FindMetricsArgs) -> list[Metric]:
        pass
