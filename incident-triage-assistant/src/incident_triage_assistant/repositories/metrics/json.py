from pathlib import Path

from incident_triage_assistant.tools.query_metrics.schema import Metric

from .base import MetricsRepository
from .schema import FindMetricsArgs

METRICS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "metrics.jsonl"
)


class JSONMetricsRepository(MetricsRepository):
    def _read_metrics(self) -> list[Metric]:
        metrics = []

        with open(METRICS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    metric = Metric.model_validate_json(line)
                    metrics.append(metric)

        return metrics

    def find(self, args: FindMetricsArgs) -> list[Metric]:
        all_metrics = self._read_metrics()

        metrics = [
            metric
            for metric in all_metrics
            if metric.service == args.service
            and metric.environment == args.environment
            and args.start_time <= metric.timestamp
            and metric.timestamp <= args.end_time
        ]

        return sorted(metrics, key=lambda metric: metric.timestamp)
