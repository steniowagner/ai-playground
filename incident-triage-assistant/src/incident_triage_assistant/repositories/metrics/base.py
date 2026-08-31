from abc import ABC, abstractmethod

from incident_triage_assistant.tools.query_metrics.schema import Metric

from .schema import FindMetricsArgs


class MetricsRepository(ABC):
    @abstractmethod
    def find(self, args: FindMetricsArgs) -> list[Metric]:
        pass
