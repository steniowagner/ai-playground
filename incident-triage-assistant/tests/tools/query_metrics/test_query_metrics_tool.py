from unittest.mock import Mock

import pytest
from incident_triage_assistant.repositories.metrics.base import MetricsRepository
from incident_triage_assistant.tools.query_metrics.schema import Metric
from incident_triage_assistant.tools.query_metrics.tool import QueryMetricsTool
from incident_triage_assistant.tools.types import ToolErrorResponse, ToolSuccessResponse


def metric() -> Metric:
    return Metric.model_validate(
        {
            "metric_id": "metric-1",
            "timestamp": "2026-08-20T10:10:00Z",
            "service": "checkout-api",
            "environment": "production",
            "values": {"error_rate": 0.04},
        }
    )


def valid_args() -> dict[str, object]:
    return {
        "service": "checkout-api",
        "environment": "production",
        "metric_names": ["error_rate", "queue_depth"],
        "start_time": "2026-08-20T10:00:00Z",
        "end_time": "2026-08-20T10:30:00Z",
    }


def test_builds_series_and_reports_metrics_without_values() -> None:
    repository = Mock(spec=MetricsRepository)
    repository.find.return_value = [metric()]
    response = QueryMetricsTool(repository)(valid_args())
    assert isinstance(response, ToolSuccessResponse)
    assert [point.value for point in response.data.series["error_rate"]] == [0.04]
    assert response.data.series["queue_depth"] == []
    assert response.data.missing_metric_names == {"queue_depth"}


def test_forwards_repository_query_context() -> None:
    repository = Mock(spec=MetricsRepository)
    repository.find.return_value = []
    QueryMetricsTool(repository)(valid_args())
    args = repository.find.call_args.args[0]
    assert (args.service, args.environment, args.metric_names) == (
        "checkout-api",
        "production",
        {"error_rate", "queue_depth"},
    )


@pytest.mark.parametrize(
    "args",
    [
        {},
        valid_args() | {"metric_names": []},
        valid_args() | {"metric_names": ["unknown"]},
        valid_args() | {"end_time": "2026-08-20T09:00:00Z"},
    ],
)
def test_rejects_invalid_arguments_without_querying_repository(
    args: dict[str, object],
) -> None:
    repository = Mock(spec=MetricsRepository)
    response = QueryMetricsTool(repository)(args)
    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"
    repository.find.assert_not_called()
