from pathlib import Path

from incident_triage_assistant_langchain.tools.query_metrics.schema import Metric
from pydantic import ValidationError

from ..exceptions import RepositoryDataError, RepositoryUnavailable
from .base import MetricsRepository
from .schema import FindMetricsArgs

METRICS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "metrics.jsonl"
)


class JSONMetricsRepository(MetricsRepository):
    def _parse_fixture(self, fixture_str: str) -> Metric:
        try:
            return Metric.model_validate_json(fixture_str)
        except ValidationError as exc:
            raise RepositoryDataError("Metrics repository data is invalid.") from exc

    def _read_metrics(self) -> list[Metric]:
        metrics: list[Metric] = []

        try:
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        metric = self._parse_fixture(line)
                        metrics.append(metric)
        except UnicodeDecodeError as exc:
            raise RepositoryDataError(
                "Metrics repository contains invalid text data."
            ) from exc
        except OSError as exc:
            raise RepositoryUnavailable("Metrics repository is unavailable.") from exc

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
