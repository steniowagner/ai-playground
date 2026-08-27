from pathlib import Path
from typing import Any

from incident_triage_assistant.domain.types import (
    ServiceMetric,
)
from incident_triage_assistant.tools.tool_response import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from pydantic import ValidationError

from .schema import Metric, MetricSeries, QueryMetricsArgs, QueryMetricsResult

METRICS_FILE = (
    Path(__file__).resolve().parents[4] / "data" / "fixtures" / "metrics.jsonl"
)


def read_metrics() -> list[Metric]:
    metrics = []

    with open(METRICS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                metric = Metric.model_validate_json(line)
                metrics.append(metric)

    return metrics


def get_series(args: QueryMetricsArgs, metrics: list[Metric]) -> MetricSeries:
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


def get_missing_metrics(
    args: QueryMetricsArgs, series: MetricSeries
) -> set[ServiceMetric]:
    missing_metrics = set()
    for metric_name in args.metric_names:
        if len(series[metric_name]) == 0:
            missing_metrics.add(metric_name)

    return missing_metrics


def find_metrics(args: QueryMetricsArgs) -> list[Metric]:
    all_metrics = read_metrics()

    metrics = [
        metric
        for metric in all_metrics
        if metric.service == args.service
        and metric.environment == args.environment
        and args.start_time <= metric.timestamp
        and metric.timestamp <= args.end_time
    ]

    # This is a time-series, that's why the sorting is ASC
    return sorted(metrics, key=lambda x: x.timestamp)


def query_metrics(raw_args: dict[str, Any]) -> ToolResponse[QueryMetricsResult]:
    try:
        args = QueryMetricsArgs.model_validate(raw_args)
    except ValidationError:
        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="INVALID_ARGUMENT", message=f"Invalid arguments '{raw_args}'"
            ),
        )

    metrics = find_metrics(args)
    series = get_series(args, metrics)
    missing_metrics = get_missing_metrics(args, series)

    result = QueryMetricsResult(
        service=args.service,
        environment=args.environment,
        start_time=args.start_time,
        end_time=args.end_time,
        requested_metric_names=args.metric_names,
        missing_metric_names=missing_metrics,
        series=series,
    )

    return ToolSuccessResponse(ok=True, data=result)
