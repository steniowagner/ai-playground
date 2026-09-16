from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import triage_ops.repositories.deployments.json as deployments_json
import triage_ops.repositories.feature_flags.json as feature_flags_json
import triage_ops.repositories.incidents.json as incidents_json
import triage_ops.repositories.logs.json as logs_json
import triage_ops.repositories.maintenance_windows.json as maintenance_json
import triage_ops.repositories.metrics.json as metrics_json
import triage_ops.repositories.runbooks.json as runbooks_json
import triage_ops.repositories.services.json as services_json
from triage_ops.repositories import RepositoryDataError, RepositoryUnavailable
from triage_ops.repositories.deployments import (
    FindDeploymentsArgs,
    JSONDeploymentsRepository,
)
from triage_ops.repositories.feature_flags import (
    FindFeatureFlagsArgs,
    JSONFeatureFlagsRepository,
)
from triage_ops.repositories.incidents import JSONIncidentRepository
from triage_ops.repositories.logs import FindLogsArgs, JSONLogsRepository
from triage_ops.repositories.maintenance_windows import (
    FindMaintenanceWindowsArgs,
    JSONMaintenanceWindowsRepository,
)
from triage_ops.repositories.metrics import FindMetricsArgs, JSONMetricsRepository
from triage_ops.repositories.runbooks import FindRunbookByIdArgs, JSONRunbooksRepository
from triage_ops.repositories.services import FindServiceArgs, JSONServicesRepository

from tests.support.factories import (
    at,
    make_incident,
)
from tests.support.factories import (
    make_deployment as deployment,
)
from tests.support.factories import (
    make_feature_flag as feature_flag,
)
from tests.support.factories import (
    make_log as log,
)
from tests.support.factories import (
    make_maintenance_window as maintenance_window,
)
from tests.support.factories import (
    make_metric as metric,
)
from tests.support.factories import (
    make_service_context as service,
)

pytestmark = pytest.mark.unit


class TestRepositoryFixtureContract:
    @pytest.mark.parametrize(
        ("repository", "reader_name"),
        [
            (JSONIncidentRepository(), "_read_incidents"),
            (JSONServicesRepository(), "_read_services"),
            (JSONDeploymentsRepository(), "_read_deployments"),
            (JSONFeatureFlagsRepository(), "_read_feature_flags"),
            (JSONMaintenanceWindowsRepository(), "_read_maintenance_windows"),
            (JSONLogsRepository(), "_read_logs"),
            (JSONMetricsRepository(), "_read_metrics"),
        ],
    )
    def test_bundled_fixture_loads(self, repository: object, reader_name: str) -> None:
        records = getattr(repository, reader_name)()

        assert records

    @pytest.mark.parametrize(
        "repository",
        [
            JSONIncidentRepository(),
            JSONServicesRepository(),
            JSONDeploymentsRepository(),
            JSONFeatureFlagsRepository(),
            JSONMaintenanceWindowsRepository(),
        ],
    )
    def test_structured_fixture_rejects_invalid_schema(self, repository: Any) -> None:
        with pytest.raises(RepositoryDataError) as error:
            repository._parse_fixture({"schema_version": "unsupported"})

        assert error.value.retryable is False

    @pytest.mark.parametrize(
        ("module", "path_name", "repository", "reader_name"),
        [
            (
                incidents_json,
                "INCIDENTS_FILE",
                JSONIncidentRepository(),
                "_read_incidents",
            ),
            (
                services_json,
                "SERVICES_FILE",
                JSONServicesRepository(),
                "_read_services",
            ),
            (
                deployments_json,
                "DEPLOYMENTS_FILE",
                JSONDeploymentsRepository(),
                "_read_deployments",
            ),
            (
                feature_flags_json,
                "FEATURE_FLAGS_FILE",
                JSONFeatureFlagsRepository(),
                "_read_feature_flags",
            ),
            (
                maintenance_json,
                "MAINTENANCE_WINDOWS_FILE",
                JSONMaintenanceWindowsRepository(),
                "_read_maintenance_windows",
            ),
            (logs_json, "LOGS_FILE", JSONLogsRepository(), "_read_logs"),
            (metrics_json, "METRICS_FILE", JSONMetricsRepository(), "_read_metrics"),
        ],
    )
    def test_missing_fixture_is_retryable_unavailable_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        module: object,
        path_name: str,
        repository: object,
        reader_name: str,
    ) -> None:
        monkeypatch.setattr(module, path_name, tmp_path / "missing")

        with pytest.raises(RepositoryUnavailable) as error:
            getattr(repository, reader_name)()

        assert error.value.retryable is True

    @pytest.mark.parametrize(
        ("module", "path_name", "repository", "reader_name", "contents"),
        [
            (
                incidents_json,
                "INCIDENTS_FILE",
                JSONIncidentRepository(),
                "_read_incidents",
                "{bad json",
            ),
            (
                services_json,
                "SERVICES_FILE",
                JSONServicesRepository(),
                "_read_services",
                "{bad json",
            ),
            (
                deployments_json,
                "DEPLOYMENTS_FILE",
                JSONDeploymentsRepository(),
                "_read_deployments",
                "{bad json",
            ),
            (
                feature_flags_json,
                "FEATURE_FLAGS_FILE",
                JSONFeatureFlagsRepository(),
                "_read_feature_flags",
                "{bad json",
            ),
            (
                maintenance_json,
                "MAINTENANCE_WINDOWS_FILE",
                JSONMaintenanceWindowsRepository(),
                "_read_maintenance_windows",
                "{bad json",
            ),
            (logs_json, "LOGS_FILE", JSONLogsRepository(), "_read_logs", "{bad json"),
            (
                metrics_json,
                "METRICS_FILE",
                JSONMetricsRepository(),
                "_read_metrics",
                "{bad json",
            ),
        ],
    )
    def test_malformed_fixture_is_non_retryable_data_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        module: object,
        path_name: str,
        repository: object,
        reader_name: str,
        contents: str,
    ) -> None:
        fixture = tmp_path / "fixture"
        fixture.write_text(contents, encoding="utf-8")
        monkeypatch.setattr(module, path_name, fixture)

        with pytest.raises(RepositoryDataError) as error:
            getattr(repository, reader_name)()

        assert error.value.retryable is False


class TestIncidentRepository:
    def test_finds_exact_incident_and_removes_fixture_truth(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        expected = make_incident()
        repository = JSONIncidentRepository()
        monkeypatch.setattr(repository, "_read_incidents", lambda: [expected])

        result = repository.find_by_id("INC-1042")

        assert result == expected
        assert "fixture_truth" not in result.model_fields_set  # type: ignore[union-attr]

    @pytest.mark.parametrize("incident_id", ["INC-9999", "inc-1042", "1042"])
    def test_unknown_or_non_exact_id_returns_none(
        self, monkeypatch: pytest.MonkeyPatch, incident_id: str
    ) -> None:
        repository = JSONIncidentRepository()
        monkeypatch.setattr(repository, "_read_incidents", lambda: [make_incident()])

        assert repository.find_by_id(incident_id) is None


class TestServicesRepository:
    def test_matches_exact_service_and_supported_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = JSONServicesRepository()
        expected = service(environments=["production", "staging"])
        monkeypatch.setattr(repository, "_read_services", lambda: [expected])

        result = repository.find(
            FindServiceArgs(service="checkout-api", environment="staging")
        )

        assert result == expected
        assert result.owner_team == "payments"  # type: ignore[union-attr]
        assert result.dependencies == ["payment-adapter"]  # type: ignore[union-attr]
        assert result.runbook_ids == ["RB-CHECKOUT-ERRORS"]  # type: ignore[union-attr]

    @pytest.mark.parametrize(
        ("name", "environment"),
        [("unknown", "production"), ("checkout-api", "staging")],
    )
    def test_returns_none_when_service_does_not_match(
        self,
        monkeypatch: pytest.MonkeyPatch,
        name: str,
        environment: str,
    ) -> None:
        repository = JSONServicesRepository()
        monkeypatch.setattr(repository, "_read_services", lambda: [service()])

        assert (
            repository.find(
                FindServiceArgs(
                    service=name,
                    environment=environment,  # type: ignore[arg-type]
                )
            )
            is None
        )


class TestDeploymentsRepository:
    def test_filters_overlap_and_sorts_newest_completion_first(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = JSONDeploymentsRepository()
        records = [
            deployment("old", started_at=at(13), completed_at=at(13, 30)),
            deployment("new", started_at=at(14, 10), completed_at=at(14, 20)),
            deployment("boundary-before", started_at=at(13), completed_at=at(14)),
            deployment("boundary-after", started_at=at(15), completed_at=at(15, 10)),
            deployment("other-service", service="catalog-api"),
            deployment("other-environment", environment="staging"),
        ]
        monkeypatch.setattr(repository, "_read_deployments", lambda: records)

        result = repository.find(
            FindDeploymentsArgs(
                service="checkout-api",
                environment="production",
                started_at=at(14),
                completed_at=at(15),
            )
        )

        assert [item.deployment_id for item in result] == ["new"]

    def test_returns_empty_list_when_nothing_matches(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = JSONDeploymentsRepository()
        monkeypatch.setattr(repository, "_read_deployments", list)

        assert (
            repository.find(
                FindDeploymentsArgs(
                    service="checkout-api",
                    environment="production",
                    started_at=at(14),
                    completed_at=at(15),
                )
            )
            == []
        )


class TestFeatureFlagsRepository:
    def test_filters_service_environment_and_sorts_by_flag(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = JSONFeatureFlagsRepository()
        records = [
            feature_flag("z-flag"),
            feature_flag("a-flag"),
            feature_flag("staging-flag", environment="staging"),
            feature_flag("catalog-flag", service="catalog-api"),
        ]
        monkeypatch.setattr(repository, "_read_feature_flags", lambda: records)

        result = repository.find(
            FindFeatureFlagsArgs(
                service="checkout-api", environment="production", flag_name=None
            )
        )

        assert [item.flag for item in result] == ["a-flag", "z-flag"]

    def test_applies_exact_flag_name_filter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = JSONFeatureFlagsRepository()
        monkeypatch.setattr(
            repository,
            "_read_feature_flags",
            lambda: [feature_flag("target"), feature_flag("target-extra")],
        )

        result = repository.find(
            FindFeatureFlagsArgs(
                service="checkout-api",
                environment="production",
                flag_name="target",
            )
        )

        assert [item.flag for item in result] == ["target"]


class TestLogsRepository:
    def args(self, **overrides: Any) -> FindLogsArgs:
        values: dict[str, Any] = {
            "service": "checkout-api",
            "environment": "production",
            "contains": None,
            "limit": 50,
            "severity": None,
            "start_time": at(14),
            "end_time": at(15),
        }
        values.update(overrides)
        return FindLogsArgs(**values)

    def test_filters_all_fields_and_includes_time_boundaries(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = JSONLogsRepository()
        records = [
            log("end", at(15), severity="WARN", message="needle at end"),
            log("start", at(14), severity="ERROR", message="needle at start"),
            log("wrong-message", at(14, 10), message="different"),
            log("wrong-severity", at(14, 20), severity="INFO", message="needle"),
            log("wrong-service", at(14, 30), service="catalog-api", message="needle"),
            log("before", at(13, 59), message="needle"),
        ]
        monkeypatch.setattr(repository, "_read_logs", lambda: records)

        result = repository.find(
            self.args(contains="needle", severity={"ERROR", "WARN"})
        )

        assert [item.log_id for item in result] == ["start", "end"]

    def test_applies_limit_after_chronological_sort(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = JSONLogsRepository()
        monkeypatch.setattr(
            repository,
            "_read_logs",
            lambda: [log("later", at(14, 20)), log("earlier", at(14, 10))],
        )

        result = repository.find(self.args(limit=1))

        assert [item.log_id for item in result] == ["earlier"]

    def test_contains_filter_is_case_sensitive(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = JSONLogsRepository()
        monkeypatch.setattr(
            repository, "_read_logs", lambda: [log("one", at(14), message="Error")]
        )

        assert repository.find(self.args(contains="error")) == []


class TestMetricsRepository:
    def test_filters_service_environment_and_includes_time_boundaries(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = JSONMetricsRepository()
        records = [
            metric("end", at(15)),
            metric("start", at(14)),
            metric("middle", at(14, 30)),
            metric("before", at(13, 59)),
            metric("other-service", at(14), service="catalog-api"),
            metric("other-environment", at(14), environment="staging"),
        ]
        monkeypatch.setattr(repository, "_read_metrics", lambda: records)

        result = repository.find(
            FindMetricsArgs(
                service="checkout-api",
                environment="production",
                metric_names={"error_rate"},
                start_time=at(14),
                end_time=at(15),
            )
        )

        assert [item.metric_id for item in result] == ["start", "middle", "end"]

    def test_returns_empty_list_when_nothing_matches(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = JSONMetricsRepository()
        monkeypatch.setattr(repository, "_read_metrics", list)

        result = repository.find(
            FindMetricsArgs(
                service="checkout-api",
                environment="production",
                metric_names={"queue_depth"},
                start_time=at(14),
                end_time=at(15),
            )
        )

        assert result == []


class TestMaintenanceWindowsRepository:
    def test_filters_overlap_service_environment_and_cancelled_windows(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repository = JSONMaintenanceWindowsRepository()
        records = [
            maintenance_window("later", start_time=at(14, 30), end_time=at(15, 30)),
            maintenance_window("earlier", start_time=at(13, 30), end_time=at(14, 30)),
            maintenance_window("boundary-before", start_time=at(13), end_time=at(14)),
            maintenance_window("boundary-after", start_time=at(15), end_time=at(16)),
            maintenance_window("cancelled", status="cancelled"),
            maintenance_window("other-service", services=["catalog-api"]),
            maintenance_window("other-environment", environment="staging"),
        ]
        monkeypatch.setattr(repository, "_read_maintenance_windows", lambda: records)

        result = repository.find(
            FindMaintenanceWindowsArgs(
                service="checkout-api",
                environment="production",
                start_time=at(14),
                end_time=at(15),
            )
        )

        assert [item.maintenance_id for item in result] == ["earlier", "later"]


class TestRunbooksRepository:
    def test_lists_only_markdown_files_and_returns_exact_runbook(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        (tmp_path / "RB-CHECKOUT.md").write_text("# Safe runbook", encoding="utf-8")
        (tmp_path / "ignored.txt").write_text("ignored", encoding="utf-8")
        monkeypatch.setattr(runbooks_json, "RUNBOOKS_DIR", tmp_path)
        repository = JSONRunbooksRepository()

        result = repository.find_by_id(FindRunbookByIdArgs(runbook_id="RB-CHECKOUT"))

        assert result == "# Safe runbook"

    def test_unknown_runbook_returns_none(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(runbooks_json, "RUNBOOKS_DIR", tmp_path)

        assert (
            JSONRunbooksRepository().find_by_id(
                FindRunbookByIdArgs(runbook_id="UNKNOWN")
            )
            is None
        )

    def test_missing_directory_is_retryable_unavailable_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(runbooks_json, "RUNBOOKS_DIR", tmp_path / "missing")

        with pytest.raises(RepositoryUnavailable) as error:
            JSONRunbooksRepository().find_by_id(
                FindRunbookByIdArgs(runbook_id="RB-CHECKOUT")
            )

        assert error.value.retryable is True

    def test_invalid_text_is_non_retryable_data_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        runbook = tmp_path / "RB-BINARY.md"
        runbook.write_bytes(b"\xff\xfe")
        monkeypatch.setattr(runbooks_json, "RUNBOOKS_DIR", tmp_path)

        with pytest.raises(RepositoryDataError) as error:
            JSONRunbooksRepository().find_by_id(
                FindRunbookByIdArgs(runbook_id="RB-BINARY")
            )

        assert error.value.retryable is False
