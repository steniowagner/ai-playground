from unittest.mock import Mock

import pytest
from incident_triage_assistant.repositories.logs.base import LogsRepository
from incident_triage_assistant.tools.query_logs.schema import Log
from incident_triage_assistant.tools.query_logs.tool import QueryLogsTool
from incident_triage_assistant.tools.types import ToolErrorResponse, ToolSuccessResponse


def log() -> Log:
    return Log.model_validate(
        {
            "log_id": "log-1",
            "timestamp": "2026-08-20T10:10:00Z",
            "service": "checkout-api",
            "environment": "production",
            "severity": "ERROR",
            "trace_id": "trace-1",
            "message": "Payment failed",
            "attributes": {"status": 500},
        }
    )


def valid_args() -> dict[str, object]:
    return {
        "service": "checkout-api",
        "environment": "production",
        "contains": "Payment",
        "severity": ["ERROR"],
        "limit": 10,
        "start_time": "2026-08-20T10:00:00Z",
        "end_time": "2026-08-20T10:30:00Z",
    }


def test_returns_repository_results_and_forwards_all_filters() -> None:
    repository = Mock(spec=LogsRepository)
    repository.find.return_value = [log()]
    response = QueryLogsTool(repository)(valid_args())
    assert isinstance(response, ToolSuccessResponse)
    assert response.data.logs == [log()]
    args = repository.find.call_args.args[0]
    assert (args.contains, args.severity, args.limit) == ("Payment", {"ERROR"}, 10)


def test_null_severity_is_forwarded_as_no_filter() -> None:
    repository = Mock(spec=LogsRepository)
    repository.find.return_value = []
    args = valid_args() | {"severity": None}
    QueryLogsTool(repository)(args)
    assert repository.find.call_args.args[0].severity is None


@pytest.mark.parametrize(
    "args",
    [
        {},
        valid_args() | {"severity": []},
        valid_args() | {"limit": 51},
        valid_args() | {"end_time": "2026-08-20T09:00:00Z"},
    ],
)
def test_rejects_invalid_arguments_without_querying_repository(
    args: dict[str, object],
) -> None:
    repository = Mock(spec=LogsRepository)
    response = QueryLogsTool(repository)(args)
    assert isinstance(response, ToolErrorResponse)
    assert response.error.code == "INVALID_ARGUMENT"
    repository.find.assert_not_called()
