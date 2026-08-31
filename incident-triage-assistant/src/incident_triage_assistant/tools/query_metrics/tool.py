from typing import Any

from incident_triage_assistant.domain.types import (
    ServiceMetric,
)
from incident_triage_assistant.repositories.metrics.base import MetricsRepository
from incident_triage_assistant.repositories.metrics.schema import FindMetricsArgs
from incident_triage_assistant.tools.types import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import Metric, MetricSeries, QueryMetricsArgs, QueryMetricsResult


class QueryMetricsTool:
    def __init__(self, repository: MetricsRepository) -> None:
        self._repository = repository

    def _get_series(
        self, args: QueryMetricsArgs, metrics: list[Metric]
    ) -> MetricSeries:
        series = {}
        for metric_name in args.metric_names:
            series[metric_name] = []

        for metric_name in args.metric_names:
            for metric in metrics:
                metric_value = getattr(metric.values, metric_name)
                if metric_value is not None:
                    series[metric_name].append(
                        {
                            "metric_id": metric.metric_id,
                            "timestamp": metric.timestamp,
                            "value": metric_value,
                        }
                    )

        return series

    def _get_missing_metrics(
        self, args: QueryMetricsArgs, series: MetricSeries
    ) -> set[ServiceMetric]:
        missing_metrics = set()
        for metric_name in args.metric_names:
            if len(series[metric_name]) == 0:
                missing_metrics.add(metric_name)

        return missing_metrics

    def __call__(self, raw_args: dict[str, Any]) -> ToolResponse[QueryMetricsResult]:
        try:
            args = QueryMetricsArgs.model_validate(raw_args)
        except ValidationError:
            return ToolErrorResponse(
                ok=False,
                error=ToolErrorResponseDetail(
                    code="INVALID_ARGUMENT", message=f"Invalid arguments '{raw_args}'"
                ),
            )

        metrics = self._repository.find(
            FindMetricsArgs(
                service=args.service,
                environment=args.environment,
                metric_names=args.metric_names,
                start_time=args.start_time,
                end_time=args.end_time,
            )
        )
        series = self._get_series(args, metrics)
        missing_metrics = self._get_missing_metrics(args, series)

        return ToolSuccessResponse(
            ok=True,
            data=QueryMetricsResult(
                service=args.service,
                environment=args.environment,
                start_time=args.start_time,
                end_time=args.end_time,
                requested_metric_names=args.metric_names,
                missing_metric_names=missing_metrics,
                series=series,
            ),
        )
