from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock

import pytest
from pydantic import BaseModel, ValidationError
from triage_ops.domain import (
    Deployment,
    FeatureFlag,
    Log,
    MaintenanceWindow,
    Metric,
    MetricValues,
    Service,
)
from triage_ops.repositories import RepositoryDataError, RepositoryUnavailable
from triage_ops.repositories.deployments import (
    DeploymentsRepository,
    FindDeploymentsArgs,
)
from triage_ops.repositories.feature_flags import (
    FeatureFlagsRepository,
    FindFeatureFlagsArgs,
)
from triage_ops.repositories.incidents import IncidentRepository
from triage_ops.repositories.logs import FindLogsArgs, LogsRepository
from triage_ops.repositories.maintenance_windows import (
    FindMaintenanceWindowsArgs,
    MaintenanceWindowsRepository,
)
from triage_ops.repositories.metrics import FindMetricsArgs, MetricsRepository
from triage_ops.repositories.runbooks import FindRunbookByIdArgs, RunbooksRepository
from triage_ops.repositories.services import FindServiceArgs, ServicesRepository
from triage_ops.tools import ToolErrorResponse, ToolNames, ToolSuccessResponse
from triage_ops.tools.bootstrap_tools import BootstrapToolsArgs, bootstrap_tools
from triage_ops.tools.complete_investigation import CompleteInvestigationTool
from triage_ops.tools.complete_investigation.schema import CompleteInvestigationArgs
from triage_ops.tools.get_feature_flags import GetFeatureFlagsTool
from triage_ops.tools.get_feature_flags.schema import GetFeatureFlagsArgs
from triage_ops.tools.get_incident import GetIncidentTool
from triage_ops.tools.get_incident.schema import GetIncidentArgs
from triage_ops.tools.get_incidents import GetIncidentsTool
from triage_ops.tools.get_incidents.schema import GetIncidentsArgs
from triage_ops.tools.get_maintenance_windows import GetMaintenanceWindowsTool
from triage_ops.tools.get_maintenance_windows.schema import GetMaintenanceWindowsArgs
from triage_ops.tools.get_recent_deployments import GetRecentDeploymentsTool
from triage_ops.tools.get_recent_deployments.schema import GetRecentDeploymentsArgs
from triage_ops.tools.get_runbook import GetRunbookTool
from triage_ops.tools.get_service_context import GetServiceContextTool
from triage_ops.tools.query_logs import QueryLogsTool
from triage_ops.tools.query_logs.schema import QueryLogsArgs
from triage_ops.tools.query_metrics import QueryMetricsTool
from triage_ops.tools.query_metrics.schema import QueryMetricsArgs

from tests.support.factories import make_incident

pytestmark = pytest.mark.unit


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 7, 10, hour, minute, tzinfo=UTC)


def make_flag() -> FeatureFlag:
    return FeatureFlag(
        flag="checkout_require_billing_country",
        service="checkout-api",
        environment="production",
        enabled=True,
        owner_team="payments",
        changed_at=at(14, 5),
        changed_by_deployment="dep-882",
    )


def make_window() -> MaintenanceWindow:
    return MaintenanceWindow(
        maintenance_id="MW-100",
        title="Database maintenance",
        services=["checkout-api"],
        environment="production",
        start_time=at(14),
        end_time=at(15),
        expected_effects=["Elevated latency"],
        approved_by="ops",
        status="in_progress",
    )


def make_deployment() -> Deployment:
    return Deployment(
        deployment_id="dep-882",
        service="checkout-api",
        environment="production",
        version="2026.07.10.1",
        commit="89d3c14",
        started_at=at(13, 58),
        completed_at=at(14, 5),
        status="succeeded",
        summary="Require billing country",
    )


def make_service() -> Service:
    return Service(
        service="checkout-api",
        display_name="Checkout API",
        description="Coordinates checkout.",
        tier=1,
        owner_team="payments",
        on_call="payments-primary",
        environments=["production", "staging"],
        dependencies=["payment-adapter"],
        runbook_ids=["RB-CHECKOUT-ERRORS"],
        slo={"availability_percent": 99.95},
    )


def make_log() -> Log:
    return Log(
        log_id="log-1",
        timestamp=at(14, 10),
        service="checkout-api",
        environment="production",
        severity="ERROR",
        trace_id="trace-1",
        message="OrderMappingError",
        attributes={"http_status": 500},
    )


def make_metric(
    metric_id: str = "metric-1",
    *,
    error_rate: float | None = 8.4,
    queue_depth: int | None = None,
) -> Metric:
    return Metric(
        metric_id=metric_id,
        timestamp=at(14, 10),
        service="checkout-api",
        environment="production",
        values=MetricValues(error_rate=error_rate, queue_depth=queue_depth),
    )


COMMON_SERVICE_INPUT = {
    "service": "checkout-api",
    "environment": "production",
}
TIME_INPUT = {
    **COMMON_SERVICE_INPUT,
    "start_time": at(14),
    "end_time": at(15),
}


@dataclass(frozen=True)
class ToolCase:
    tool_class: type
    repository_class: type
    repository_method: str
    tool_input: dict[str, Any]
    repository_args_class: type[BaseModel]
    repository_result: Any
    result_attribute: str
    expected_result: Any


TOOL_CASES = [
    ToolCase(
        GetIncidentTool,
        IncidentRepository,
        "find_by_id",
        {"incident_id": "INC-1042"},
        GetIncidentArgs,
        make_incident(),
        "incident",
        make_incident(),
    ),
    ToolCase(
        GetFeatureFlagsTool,
        FeatureFlagsRepository,
        "find",
        {**COMMON_SERVICE_INPUT, "flag_name": "checkout_require_billing_country"},
        FindFeatureFlagsArgs,
        [make_flag()],
        "feature_flags",
        [make_flag()],
    ),
    ToolCase(
        GetMaintenanceWindowsTool,
        MaintenanceWindowsRepository,
        "find",
        TIME_INPUT,
        FindMaintenanceWindowsArgs,
        [make_window()],
        "maintenance_windows",
        [make_window()],
    ),
    ToolCase(
        GetRecentDeploymentsTool,
        DeploymentsRepository,
        "find",
        {
            **COMMON_SERVICE_INPUT,
            "started_at": at(14),
            "completed_at": at(15),
        },
        FindDeploymentsArgs,
        [make_deployment()],
        "deployments",
        [make_deployment()],
    ),
    ToolCase(
        GetRunbookTool,
        RunbooksRepository,
        "find_by_id",
        {"runbook_id": "RB-CHECKOUT-ERRORS"},
        FindRunbookByIdArgs,
        "# Checkout errors\nFollow the diagnostic steps.",
        "content",
        "# Checkout errors\nFollow the diagnostic steps.",
    ),
    ToolCase(
        GetServiceContextTool,
        ServicesRepository,
        "find",
        COMMON_SERVICE_INPUT,
        FindServiceArgs,
        make_service(),
        "service",
        make_service(),
    ),
    ToolCase(
        QueryLogsTool,
        LogsRepository,
        "find",
        {
            **TIME_INPUT,
            "contains": "OrderMappingError",
            "limit": 10,
            "severity": {"ERROR"},
        },
        FindLogsArgs,
        [make_log()],
        "logs",
        [make_log()],
    ),
]


class TestReadOnlyToolSuccessContract:
    @pytest.mark.parametrize(
        "case", TOOL_CASES, ids=lambda case: case.tool_class.__name__
    )
    def test_forwards_typed_arguments_and_wraps_repository_result(
        self, case: ToolCase
    ) -> None:
        repository = Mock(spec=case.repository_class)
        getattr(
            repository, case.repository_method
        ).return_value = case.repository_result
        tool = case.tool_class(repository=repository)

        response = tool.invoke(case.tool_input)

        assert isinstance(response, ToolSuccessResponse)
        assert getattr(response.data, case.result_attribute) == case.expected_result
        call = getattr(repository, case.repository_method).call_args
        if (
            case.repository_method == "find_by_id"
            and case.tool_class is GetIncidentTool
        ):
            assert call.kwargs == {"incident_id": "INC-1042"}
        else:
            forwarded_args = call.args[0]
            assert isinstance(forwarded_args, case.repository_args_class)
            for name, value in case.tool_input.items():
                assert getattr(forwarded_args, name) == value

    @pytest.mark.parametrize(
        ("tool_class", "repository_class", "method", "tool_input"),
        [
            (
                GetIncidentTool,
                IncidentRepository,
                "find_by_id",
                {"incident_id": "INC-1042"},
            ),
            (
                GetRunbookTool,
                RunbooksRepository,
                "find_by_id",
                {"runbook_id": "RB-UNKNOWN"},
            ),
            (
                GetServiceContextTool,
                ServicesRepository,
                "find",
                COMMON_SERVICE_INPUT,
            ),
        ],
    )
    def test_missing_resource_returns_non_retryable_not_found(
        self,
        tool_class: type,
        repository_class: type,
        method: str,
        tool_input: dict[str, Any],
    ) -> None:
        repository = Mock(spec=repository_class)
        getattr(repository, method).return_value = None

        response = tool_class(repository=repository).invoke(tool_input)

        assert isinstance(response, ToolErrorResponse)
        assert response.error.code == "NOT_FOUND"
        assert response.error.retryable is False
        assert response.error.input == tool_input


ERROR_CASES = [
    (case.tool_class, case.repository_class, case.repository_method, case.tool_input)
    for case in TOOL_CASES
] + [
    (
        QueryMetricsTool,
        MetricsRepository,
        "find",
        {**TIME_INPUT, "metric_names": {"error_rate"}},
    )
]


class TestReadOnlyToolErrorContract:
    @pytest.mark.parametrize(
        ("tool_class", "repository_class", "method", "tool_input"),
        ERROR_CASES,
        ids=lambda value: value.__name__ if isinstance(value, type) else None,
    )
    @pytest.mark.parametrize(
        ("exception", "retryable", "guidance"),
        [
            (RepositoryUnavailable("secret storage details"), True, "Retry"),
            (RepositoryDataError("secret fixture details"), False, "Do not retry"),
        ],
    )
    def test_translates_repository_failures_to_safe_error_response(
        self,
        tool_class: type,
        repository_class: type,
        method: str,
        tool_input: dict[str, Any],
        exception: Exception,
        retryable: bool,
        guidance: str,
    ) -> None:
        repository = Mock(spec=repository_class)
        getattr(repository, method).side_effect = exception
        tool = tool_class(repository=repository)

        response = tool.invoke(tool_input)

        assert isinstance(response, ToolErrorResponse)
        assert response.error.code == "EXECUTION_ERROR"
        assert response.error.retryable is retryable
        expected_input = tool.args_schema.model_validate(tool_input).model_dump(
            mode="json"
        )
        assert response.error.input == expected_input
        assert guidance in response.error.suggested_action
        assert "secret" not in response.model_dump_json()


class TestGetIncidentsTool:
    def test_returns_every_registered_incident(self) -> None:
        incidents = [
            make_incident(),
            make_incident(
                incident_id="INC-1043",
                title="Inventory processing delayed",
            ),
        ]
        repository = Mock(spec=IncidentRepository)
        repository.find_all.return_value = incidents
        tool = GetIncidentsTool(repository=repository)

        response = tool.invoke({})

        assert isinstance(response, ToolSuccessResponse)
        assert response.data.incidents == incidents
        repository.find_all.assert_called_once_with()

    def test_returns_success_when_no_incidents_are_registered(self) -> None:
        repository = Mock(spec=IncidentRepository)
        repository.find_all.return_value = []
        tool = GetIncidentsTool(repository=repository)

        response = tool.invoke({})

        assert isinstance(response, ToolSuccessResponse)
        assert response.data.incidents == []
        repository.find_all.assert_called_once_with()

    @pytest.mark.parametrize(
        ("exception", "retryable", "guidance"),
        [
            (RepositoryUnavailable("secret storage details"), True, "Retry"),
            (RepositoryDataError("secret fixture details"), False, "Do not retry"),
        ],
    )
    def test_translates_repository_failures_to_safe_error_response(
        self,
        exception: Exception,
        retryable: bool,
        guidance: str,
    ) -> None:
        repository = Mock(spec=IncidentRepository)
        repository.find_all.side_effect = exception
        tool = GetIncidentsTool(repository=repository)

        response = tool.invoke({})

        assert isinstance(response, ToolErrorResponse)
        assert response.error.code == "EXECUTION_ERROR"
        assert response.error.retryable is retryable
        assert response.error.input == {}
        assert guidance in response.error.suggested_action
        assert "secret" not in response.model_dump_json()
        repository.find_all.assert_called_once_with()


class TestQueryMetricsTool:
    def test_builds_requested_series_and_reports_missing_metrics(self) -> None:
        repository = Mock(spec=MetricsRepository)
        repository.find.return_value = [
            make_metric("metric-1", error_rate=8.4),
            make_metric("metric-2", error_rate=9.1),
        ]
        tool = QueryMetricsTool(repository=repository)

        response = tool.invoke(
            {**TIME_INPUT, "metric_names": {"error_rate", "queue_depth"}}
        )

        assert isinstance(response, ToolSuccessResponse)
        assert response.data.requested_metric_names == {"error_rate", "queue_depth"}
        assert response.data.missing_metric_names == {"queue_depth"}
        assert [point.value for point in response.data.series["error_rate"]] == [
            8.4,
            9.1,
        ]
        assert response.data.series["queue_depth"] == []
        forwarded_args = repository.find.call_args.args[0]
        assert isinstance(forwarded_args, FindMetricsArgs)
        assert forwarded_args.metric_names == {"error_rate", "queue_depth"}


class TestToolArgumentSchemas:
    @pytest.mark.parametrize(
        ("schema", "payload"),
        [
            (
                CompleteInvestigationArgs,
                {"incident_id": "1042", "reason": "evidence_sufficient"},
            ),
            (
                CompleteInvestigationArgs,
                {"incident_id": "INC-1042", "reason": "done"},
            ),
            (GetIncidentArgs, {"incident_id": "inc-1042"}),
            (GetIncidentsArgs, {"incident_id": "INC-1042"}),
            (
                GetFeatureFlagsArgs,
                {**COMMON_SERVICE_INPUT, "flag_name": ""},
            ),
            (
                GetRecentDeploymentsArgs,
                {
                    **COMMON_SERVICE_INPUT,
                    "started_at": at(15),
                    "completed_at": at(14),
                },
            ),
            (
                GetMaintenanceWindowsArgs,
                {**COMMON_SERVICE_INPUT, "start_time": at(14), "end_time": at(14)},
            ),
            (
                GetMaintenanceWindowsArgs,
                {
                    **COMMON_SERVICE_INPUT,
                    "start_time": at(14),
                    "end_time": datetime(2026, 7, 11, 15, tzinfo=UTC),
                },
            ),
            (
                QueryLogsArgs,
                {**TIME_INPUT, "contains": None, "limit": 0, "severity": None},
            ),
            (
                QueryLogsArgs,
                {**TIME_INPUT, "contains": None, "limit": 51, "severity": None},
            ),
            (
                QueryLogsArgs,
                {
                    **COMMON_SERVICE_INPUT,
                    "contains": None,
                    "limit": 10,
                    "severity": None,
                    "start_time": at(13),
                    "end_time": at(15),
                },
            ),
            (
                QueryMetricsArgs,
                {**TIME_INPUT, "metric_names": set()},
            ),
            (
                QueryMetricsArgs,
                {
                    **COMMON_SERVICE_INPUT,
                    "metric_names": {"error_rate"},
                    "start_time": at(13),
                    "end_time": at(15),
                },
            ),
        ],
    )
    def test_rejects_invalid_arguments(
        self, schema: type[BaseModel], payload: dict[str, Any]
    ) -> None:
        with pytest.raises(ValidationError):
            schema.model_validate(payload)

    def test_tool_invocation_validates_before_repository_call(self) -> None:
        repository = Mock(spec=IncidentRepository)
        tool = GetIncidentTool(repository=repository)

        with pytest.raises(ValidationError):
            tool.invoke({"incident_id": "1042"})

        repository.find_by_id.assert_not_called()


class TestCompleteInvestigationTool:
    @pytest.mark.parametrize(
        "reason", ["evidence_sufficient", "incident_lookup_failed"]
    )
    def test_acknowledges_supported_completion_reason(self, reason: str) -> None:
        response = CompleteInvestigationTool().invoke(
            {"incident_id": "INC-1042", "reason": reason}
        )

        assert isinstance(response, ToolSuccessResponse)
        assert response.data.acknowledged is True


class TestToolRegistry:
    def test_registers_every_tool_name_once_with_an_argument_schema(self) -> None:
        tools = bootstrap_tools(
            BootstrapToolsArgs(
                deployments_repository=Mock(spec=DeploymentsRepository),
                feature_flags_repository=Mock(spec=FeatureFlagsRepository),
                incidents_repository=Mock(spec=IncidentRepository),
                logs_repository=Mock(spec=LogsRepository),
                maintenance_windows_repository=Mock(spec=MaintenanceWindowsRepository),
                metrics_repository=Mock(spec=MetricsRepository),
                runbooks_repository=Mock(spec=RunbooksRepository),
                services_repository=Mock(spec=ServicesRepository),
            )
        )
        names = [tool.get_name() for tool in tools]

        assert set(names) == {name.value for name in ToolNames}
        assert len(names) == len(set(names))
        assert all(tool.args_schema is not None for tool in tools)
