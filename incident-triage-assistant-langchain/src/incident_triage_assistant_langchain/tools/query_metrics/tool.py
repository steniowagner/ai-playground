import logging

from incident_triage_assistant_langchain.domain.types import (
    Environment,
)
from incident_triage_assistant_langchain.repositories.exceptions import (
    RepositoryException,
)
from incident_triage_assistant_langchain.repositories.metrics.base import (
    MetricsRepository,
)
from incident_triage_assistant_langchain.repositories.metrics.schema import (
    FindMetricsArgs,
)
from incident_triage_assistant_langchain.tools.schema import (
    ToolErrorResponse,
    ToolErrorResponseDetail,
    ToolResponse,
    ToolSuccessResponse,
)
from langchain_core.tools import BaseTool
from pydantic import AwareDatetime, BaseModel

from .schema import (
    Metric,
    MetricSeries,
    QueryMetricsArgs,
    QueryMetricsResult,
    ServiceMetric,
)


class QueryMetricsTool(BaseTool):
    name: str = "query_metrics"
    description: str = "Query selected metrics for one exact service and environment within a maximum 60-minute window. Returns timestamped measurements and evidence IDs; use the observations to investigate behavior without asking the tool to determine the root cause."
    args_schema: type[BaseModel] = QueryMetricsArgs
    repository: MetricsRepository

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

    def _handle_error(
        self,
        args: QueryMetricsArgs,
    ) -> ToolErrorResponse:
        logger = logging.getLogger(__name__)

        tool_input = {
            "service": args.service,
            "environment": args.environment,
            "contains": args.contains,
            "limit": args.limit,
            "severity": args.severity,
            "start_time": args.start_time,
            "end_time": args.end_time,
        }

        logger.exception(
            "Failed to query metrics.",
            extra=tool_input,
        )

        return ToolErrorResponse(
            ok=False,
            error=ToolErrorResponseDetail(
                code="EXECUTION_ERROR",
                message="Failed to query metrics due an internal error.",
                retryable=True,
                input=tool_input,
                suggested_action="Retry this request once. If it fails again, stop the investigation and let the user knows that it was due this error.",
            ),
        )

    def _run(
        self,
        service: str,
        environment: Environment,
        metric_names: set[ServiceMetric],
        start_time: AwareDatetime,
        end_time: AwareDatetime,
    ) -> ToolResponse[QueryMetricsResult]:
        try:
            metrics = self.repository.find(
                FindMetricsArgs(
                    service=service,
                    environment=environment,
                    metric_names=metric_names,
                    start_time=start_time,
                    end_time=end_time,
                )
            )
        except RepositoryException:
            return self._handle_error()

        query_metrics_args = QueryMetricsArgs(
            service=service,
            environment=environment,
            start_time=start_time,
            end_time=end_time,
            requested_metric_names=metric_names,
        )

        series = self._get_series(args=query_metrics_args, metrics=metrics)
        missing_metrics = self._get_missing_metrics(
            args=query_metrics_args, series=series
        )

        return ToolSuccessResponse(
            ok=True,
            data=QueryMetricsResult(
                service=service,
                environment=environment,
                start_time=start_time,
                end_time=end_time,
                requested_metric_names=metric_names,
                missing_metric_names=missing_metrics,
                series=series,
            ),
        )
