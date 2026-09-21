from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import UTC, datetime
from typing import Any, Self
from uuid import UUID

import pytest
from sqlalchemy.dialects import postgresql
from triage_ops.db import (
    DeploymentsRecord,
    FeatureFlagsRecord,
    IncidentsRecord,
    LogsRecord,
    MaintenanceWindowsRecord,
    MetricsRecord,
    ServicesRecord,
)
from triage_ops.repositories.deployments import (
    FindDeploymentsArgs,
    PostgresDeploymentsRepository,
)
from triage_ops.repositories.feature_flags import (
    FindFeatureFlagsArgs,
    PostgresFeatureFlagsRepository,
)
from triage_ops.repositories.incidents import PostgresIncidentsRepository
from triage_ops.repositories.logs import FindLogsArgs, PostgresLogsRepository
from triage_ops.repositories.maintenance_windows import (
    FindMaintenanceWindowsArgs,
    PostgresMaintenanceWindowsRepository,
)
from triage_ops.repositories.metrics import FindMetricsArgs, PostgresMetricsRepository
from triage_ops.repositories.services import FindServiceArgs, PostgresServicesRepository

pytestmark = pytest.mark.unit


def at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 7, 10, hour, minute, tzinfo=UTC)


class ScalarRows:
    def __init__(self, records: list[Any]) -> None:
        self._records = records

    def all(self) -> list[Any]:
        return self._records


class RecordingSession(AbstractContextManager["RecordingSession"]):
    def __init__(
        self,
        *,
        records: list[Any] | None = None,
        scalar_record: Any | None = None,
        get_record: Any | None = None,
    ) -> None:
        self.records = records or []
        self.scalar_record = scalar_record
        self.get_record = get_record
        self.statements: list[Any] = []
        self.get_calls: list[tuple[type[Any], Any]] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def scalars(self, statement: Any) -> ScalarRows:
        self.statements.append(statement)
        return ScalarRows(self.records)

    def scalar(self, statement: Any) -> Any | None:
        self.statements.append(statement)
        return self.scalar_record

    def get(self, model: type[Any], key: Any) -> Any | None:
        self.get_calls.append((model, key))
        return self.get_record


def session_factory(session: RecordingSession):
    return lambda: session


def compiled(statement: Any) -> tuple[str, dict[str, Any]]:
    result = statement.compile(dialect=postgresql.dialect())
    return " ".join(str(result).split()), result.params


def deployment_record(identifier: str = "dep-882") -> DeploymentsRecord:
    return DeploymentsRecord(
        id=identifier,
        service="checkout-api",
        environment="production",
        version="2026.07.10.1",
        commit="abc1234",
        started_at=at(13, 55),
        completed_at=at(14, 5),
        status="succeeded",
        summary="Deploy checkout changes",
    )


def feature_flag_record() -> FeatureFlagsRecord:
    return FeatureFlagsRecord(
        id=UUID("10000000-0000-0000-0000-000000000001"),
        flag="checkout_require_billing_country",
        service="checkout-api",
        environment="production",
        enabled=True,
        owner_team="payments",
        changed_at=at(14, 5),
        changed_by_deployment="dep-882",
    )


def incident_record() -> IncidentsRecord:
    return IncidentsRecord(
        id="INC-1042",
        title="Checkout errors",
        environment="production",
        primary_service="checkout-api",
        alert_started_at=at(14),
        created_at=at(14, 2),
        status="investigating",
        severity="SEV2",
        reported_symptoms=["Elevated HTTP 5xx responses"],
        alert={
            "metric": "error_rate",
            "observed": 18.4,
            "threshold": 2.0,
            "unit": "percent",
        },
    )


def log_record() -> LogsRecord:
    return LogsRecord(
        id="log-1",
        timestamp=at(14, 10),
        service="checkout-api",
        environment="production",
        severity="ERROR",
        trace_id="trace-1",
        message="OrderMappingError",
        attributes={"deployment_id": "dep-882"},
    )


def maintenance_record() -> MaintenanceWindowsRecord:
    return MaintenanceWindowsRecord(
        id="MW-100",
        title="Database maintenance",
        services=["checkout-api"],
        environment="production",
        start_time=at(14),
        end_time=at(15),
        expected_effects=["Elevated latency"],
        approved_by="ops",
        status="in_progress",
    )


def metric_record() -> MetricsRecord:
    return MetricsRecord(
        id="metric-1",
        timestamp=at(14, 10),
        service="checkout-api",
        environment="production",
        values={"error_rate": 18.4, "p95_latency_ms": 900},
    )


def service_record() -> ServicesRecord:
    return ServicesRecord(
        id=UUID("10000000-0000-0000-0000-000000000002"),
        service="checkout-api",
        display_name="Checkout API",
        description="Checkout service",
        tier=1,
        owner_team="payments",
        on_call="payments-primary",
        environments=["production", "staging"],
        dependencies=["payment-adapter"],
        runbook_ids=["RB-CHECKOUT-ERRORS"],
        slo={"availability_percent": 99.95},
    )


@pytest.mark.parametrize(
    ("repository_type", "record", "identifier_attribute", "identifier"),
    [
        (
            PostgresDeploymentsRepository,
            deployment_record(),
            "deployment_id",
            "dep-882",
        ),
        (
            PostgresFeatureFlagsRepository,
            feature_flag_record(),
            "flag",
            "checkout_require_billing_country",
        ),
        (PostgresIncidentsRepository, incident_record(), "incident_id", "INC-1042"),
        (PostgresLogsRepository, log_record(), "log_id", "log-1"),
        (
            PostgresMaintenanceWindowsRepository,
            maintenance_record(),
            "maintenance_id",
            "MW-100",
        ),
        (PostgresMetricsRepository, metric_record(), "metric_id", "metric-1"),
        (PostgresServicesRepository, service_record(), "service", "checkout-api"),
    ],
)
def test_find_all_maps_every_postgres_record(
    repository_type: type[Any],
    record: Any,
    identifier_attribute: str,
    identifier: str,
) -> None:
    session = RecordingSession(records=[record])
    repository = repository_type(session_factory(session))

    result = repository.find_all()

    assert len(result) == 1
    assert getattr(result[0], identifier_attribute) == identifier
    assert len(session.statements) == 1
    sql, _ = compiled(session.statements[0])
    assert "SELECT" in sql
    assert "WHERE" not in sql


def test_incident_lookup_uses_primary_key_and_maps_nested_alert() -> None:
    session = RecordingSession(get_record=incident_record())
    repository = PostgresIncidentsRepository(session_factory(session))

    result = repository.find_by_id("INC-1042")

    assert result is not None
    assert result.incident_id == "INC-1042"
    assert result.alert.metric == "error_rate"
    assert session.get_calls == [(IncidentsRecord, "INC-1042")]


def test_incident_lookup_returns_none_for_a_missing_record() -> None:
    session = RecordingSession()

    result = PostgresIncidentsRepository(session_factory(session)).find_by_id(
        "INC-9999"
    )

    assert result is None
    assert session.get_calls == [(IncidentsRecord, "INC-9999")]


def test_deployment_find_builds_exact_service_environment_and_overlap_filters() -> None:
    session = RecordingSession(records=[deployment_record()])
    repository = PostgresDeploymentsRepository(session_factory(session))

    result = repository.find(
        FindDeploymentsArgs(
            service="checkout-api",
            environment="production",
            started_at=at(13),
            completed_at=at(15),
        )
    )

    assert result[0].deployment_id == "dep-882"
    sql, params = compiled(session.statements[0])
    assert "deployments.service =" in sql
    assert "deployments.environment =" in sql
    assert "deployments.started_at <=" in sql
    assert "deployments.completed_at >=" in sql
    assert "ORDER BY deployments.completed_at DESC" in sql
    assert {"checkout-api", "production", at(13), at(15)} <= set(params.values())


@pytest.mark.parametrize("flag_name", [None, "checkout_require_billing_country"])
def test_feature_flag_find_applies_optional_exact_name_filter(
    flag_name: str | None,
) -> None:
    session = RecordingSession(records=[feature_flag_record()])
    repository = PostgresFeatureFlagsRepository(session_factory(session))

    result = repository.find(
        FindFeatureFlagsArgs(
            service="checkout-api",
            environment="production",
            flag_name=flag_name,
        )
    )

    assert result[0].enabled is True
    sql, params = compiled(session.statements[0])
    assert "feature_flags.service =" in sql
    assert "feature_flags.environment =" in sql
    assert ("feature_flags.flag =" in sql) is (flag_name is not None)
    assert "ORDER BY feature_flags.flag ASC" in sql
    if flag_name is not None:
        assert flag_name in params.values()


def test_log_find_builds_optional_filters_order_and_limit() -> None:
    session = RecordingSession(records=[log_record()])
    repository = PostgresLogsRepository(session_factory(session))

    result = repository.find(
        FindLogsArgs(
            service="checkout-api",
            environment="production",
            contains="Mapping",
            severity={"WARN", "ERROR"},
            limit=12,
            start_time=at(14),
            end_time=at(15),
        )
    )

    assert result[0].attributes == {"deployment_id": "dep-882"}
    sql, params = compiled(session.statements[0])
    assert "logs.message LIKE" in sql
    assert "logs.severity IN" in sql
    assert "ORDER BY logs.timestamp ASC" in sql
    assert "LIMIT" in sql
    assert 12 in params.values()


def test_log_find_omits_optional_filters_when_not_requested() -> None:
    session = RecordingSession(records=[])
    repository = PostgresLogsRepository(session_factory(session))

    result = repository.find(
        FindLogsArgs(
            service="checkout-api",
            environment="production",
            contains=None,
            severity=None,
            limit=50,
            start_time=at(14),
            end_time=at(15),
        )
    )

    assert result == []
    sql, _ = compiled(session.statements[0])
    assert "logs.message LIKE" not in sql
    assert "logs.severity IN" not in sql


def test_maintenance_find_builds_overlap_and_non_cancelled_filters() -> None:
    session = RecordingSession(records=[maintenance_record()])
    repository = PostgresMaintenanceWindowsRepository(session_factory(session))

    result = repository.find(
        FindMaintenanceWindowsArgs(
            service="checkout-api",
            environment="production",
            start_time=at(14),
            end_time=at(15),
        )
    )

    assert result[0].status == "in_progress"
    sql, params = compiled(session.statements[0])
    assert "maintenance_windows.services @>" in sql
    assert "maintenance_windows.status !=" in sql
    assert "maintenance_windows.start_time <" in sql
    assert "maintenance_windows.end_time >" in sql
    assert "ORDER BY maintenance_windows.start_time ASC" in sql
    assert "cancelled" in params.values()


def test_metric_find_builds_inclusive_window_and_chronological_order() -> None:
    session = RecordingSession(records=[metric_record()])
    repository = PostgresMetricsRepository(session_factory(session))

    result = repository.find(
        FindMetricsArgs(
            service="checkout-api",
            environment="production",
            metric_names={"error_rate"},
            start_time=at(14),
            end_time=at(15),
        )
    )

    assert result[0].values.error_rate == 18.4
    sql, _ = compiled(session.statements[0])
    assert "metrics.timestamp >=" in sql
    assert "metrics.timestamp <=" in sql
    assert "ORDER BY metrics.timestamp ASC" in sql


def test_service_find_uses_scalar_and_maps_service_context() -> None:
    session = RecordingSession(scalar_record=service_record())
    repository = PostgresServicesRepository(session_factory(session))

    result = repository.find(
        FindServiceArgs(service="checkout-api", environment="production")
    )

    assert result is not None
    assert result.owner_team == "payments"
    assert result.display_name == "Checkout API"
    sql, params = compiled(session.statements[0])
    assert "services.service =" in sql
    assert "services.environments @>" in sql
    assert "checkout-api" in params.values()


def test_service_find_returns_none_when_scalar_has_no_record() -> None:
    session = RecordingSession()

    result = PostgresServicesRepository(session_factory(session)).find(
        FindServiceArgs(service="missing", environment="production")
    )

    assert result is None
