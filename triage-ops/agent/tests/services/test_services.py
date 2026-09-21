from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import Mock

import pytest
from pydantic import BaseModel, ValidationError

import triage_ops.services.schema as service_schema
from triage_ops.domain.investigation.proposals import (
    DisableFeatureFlagProposal,
    EscalateIncidentProposal,
    ProposalBase,
    RestartServiceProposal,
    RollbackDeploymentProposal,
)
from triage_ops.services import (
    Service,
    ServiceErrorResponse,
    ServiceErrorResponseDetail,
    ServiceExecutionException,
    ServiceSuccessResponse,
    bootstrap_services,
)
from triage_ops.services.disable_feature_flag import (
    DisableFeatureFlagService,
    DisableFeatureFlagServiceArgs,
)
from triage_ops.services.escalate_incident import (
    EscalateIncidentService,
    EscalateIncidentServiceArgs,
)
from triage_ops.services.restart_service import RestartService, RestartServiceArgs
from triage_ops.services.rollback_deployment import (
    RollbackDeploymentServiceArgs,
    RoolbackDeploymentService,
)

pytestmark = pytest.mark.unit


@dataclass(frozen=True)
class ServiceCase:
    registry_key: str
    proposal_class: type[ProposalBase]
    service_class: type[Service]
    args: BaseModel


SERVICE_CASES = [
    ServiceCase(
        registry_key="rollback_deployment",
        proposal_class=RollbackDeploymentProposal,
        service_class=RoolbackDeploymentService,
        args=RollbackDeploymentServiceArgs(
            service="checkout-api",
            environment="production",
            deployment_id="dep-882",
            target_deployment_id="dep-880",
        ),
    ),
    ServiceCase(
        registry_key="disable_feature_flag",
        proposal_class=DisableFeatureFlagProposal,
        service_class=DisableFeatureFlagService,
        args=DisableFeatureFlagServiceArgs(
            service="checkout-api",
            environment="production",
            flag_key="checkout_require_billing_country",
        ),
    ),
    ServiceCase(
        registry_key="restart_service",
        proposal_class=RestartServiceProposal,
        service_class=RestartService,
        args=RestartServiceArgs(
            service="checkout-api",
            environment="production",
            strategy="rolling",
        ),
    ),
    ServiceCase(
        registry_key="escalate_incident",
        proposal_class=EscalateIncidentProposal,
        service_class=EscalateIncidentService,
        args=EscalateIncidentServiceArgs(
            incident_id="INC-1042",
            to_severity="SEV1",
            notify_team="payments",
        ),
    ),
]


INVALID_ARGUMENT_CASES = [
    pytest.param(
        DisableFeatureFlagServiceArgs,
        {
            "service": "",
            "environment": "production",
            "flag_key": "checkout_require_billing_country",
        },
        id="disable-empty-service",
    ),
    pytest.param(
        DisableFeatureFlagServiceArgs,
        {
            "service": "checkout-api",
            "environment": "qa",
            "flag_key": "checkout_require_billing_country",
        },
        id="disable-invalid-environment",
    ),
    pytest.param(
        DisableFeatureFlagServiceArgs,
        {
            "service": "checkout-api",
            "environment": "production",
            "flag_key": "",
        },
        id="disable-empty-flag",
    ),
    pytest.param(
        RestartServiceArgs,
        {"service": "", "environment": "production", "strategy": "rolling"},
        id="restart-empty-service",
    ),
    pytest.param(
        RestartServiceArgs,
        {"service": "checkout-api", "environment": "qa", "strategy": "rolling"},
        id="restart-invalid-environment",
    ),
    pytest.param(
        RestartServiceArgs,
        {
            "service": "checkout-api",
            "environment": "production",
            "strategy": "blue-green",
        },
        id="restart-invalid-strategy",
    ),
    pytest.param(
        RollbackDeploymentServiceArgs,
        {
            "service": "",
            "environment": "production",
            "deployment_id": "dep-882",
        },
        id="rollback-empty-service",
    ),
    pytest.param(
        RollbackDeploymentServiceArgs,
        {
            "service": "checkout-api",
            "environment": "qa",
            "deployment_id": "dep-882",
        },
        id="rollback-invalid-environment",
    ),
    pytest.param(
        RollbackDeploymentServiceArgs,
        {
            "service": "checkout-api",
            "environment": "production",
            "deployment_id": "",
        },
        id="rollback-empty-deployment",
    ),
    pytest.param(
        RollbackDeploymentServiceArgs,
        {
            "service": "checkout-api",
            "environment": "production",
            "deployment_id": "dep-882",
            "target_deployment_id": "",
        },
        id="rollback-empty-target",
    ),
    pytest.param(
        EscalateIncidentServiceArgs,
        {
            "incident_id": "inc-1042",
            "to_severity": "SEV1",
            "notify_team": "payments",
        },
        id="escalate-malformed-incident",
    ),
    pytest.param(
        EscalateIncidentServiceArgs,
        {
            "incident_id": "INC-1042",
            "to_severity": "SEV0",
            "notify_team": "payments",
        },
        id="escalate-invalid-severity",
    ),
    pytest.param(
        EscalateIncidentServiceArgs,
        {
            "incident_id": "INC-1042",
            "to_severity": "SEV1",
            "notify_team": "",
        },
        id="escalate-empty-team",
    ),
]


class TestOperationalServices:
    @pytest.mark.parametrize("case", SERVICE_CASES, ids=lambda case: case.registry_key)
    def test_returns_standard_success_with_exact_serialized_arguments(
        self, monkeypatch: pytest.MonkeyPatch, case: ServiceCase
    ) -> None:
        delay = Mock()
        monkeypatch.setattr(service_schema, "sleep", delay)

        response = case.service_class().execute(case.args)

        assert isinstance(response, ServiceSuccessResponse)
        assert response.ok is True
        assert response.error is None
        assert response.data == case.args.model_dump(mode="json")
        delay.assert_called_once_with(3)

    @pytest.mark.parametrize("case", SERVICE_CASES, ids=lambda case: case.registry_key)
    def test_rejects_untyped_arguments(self, case: ServiceCase) -> None:
        with pytest.raises(TypeError, match="requires typed arguments"):
            case.service_class().execute(case.args.model_dump())  # type: ignore[arg-type]

    @pytest.mark.parametrize("case", SERVICE_CASES, ids=lambda case: case.registry_key)
    def test_converts_operational_failures_to_the_service_exception(
        self,
        monkeypatch: pytest.MonkeyPatch,
        case: ServiceCase,
    ) -> None:
        service = case.service_class()

        def fail_operation(*args: Any, **kwargs: Any) -> None:
            raise RuntimeError("sensitive provider failure")

        monkeypatch.setattr(service.logger, "warning", fail_operation)

        with pytest.raises(ServiceExecutionException) as error:
            service.execute(case.args)

        assert isinstance(error.value.__cause__, RuntimeError)
        assert "sensitive provider failure" not in str(error.value)

    @pytest.mark.parametrize("case", SERVICE_CASES, ids=lambda case: case.registry_key)
    def test_service_has_a_class_specific_logger(self, case: ServiceCase) -> None:
        service = case.service_class()

        assert service.logger.name == (
            f"{case.service_class.__module__}.{case.service_class.__name__}"
        )


class TestServiceArgumentSchemas:
    @pytest.mark.parametrize(
        ("schema", "payload"),
        INVALID_ARGUMENT_CASES,
    )
    def test_rejects_invalid_service_arguments(
        self,
        schema: type[BaseModel],
        payload: dict[str, Any],
    ) -> None:
        with pytest.raises(ValidationError):
            schema.model_validate(payload)

    @pytest.mark.parametrize("case", SERVICE_CASES, ids=lambda case: case.registry_key)
    def test_rejects_unknown_argument_fields(self, case: ServiceCase) -> None:
        payload = {**case.args.model_dump(), "unexpected": "value"}

        with pytest.raises(ValidationError):
            type(case.args).model_validate(payload)

    @pytest.mark.parametrize("case", SERVICE_CASES, ids=lambda case: case.registry_key)
    def test_typed_arguments_are_immutable(self, case: ServiceCase) -> None:
        field_name = next(iter(type(case.args).model_fields))

        with pytest.raises(ValidationError):
            setattr(case.args, field_name, "changed")

    def test_accepts_supported_optional_and_strategy_variants(self) -> None:
        rollback = RollbackDeploymentServiceArgs(
            service="checkout-api",
            environment="production",
            deployment_id="dep-882",
            target_deployment_id=None,
        )
        escalation = EscalateIncidentServiceArgs(
            incident_id="INC-1042",
            to_severity="SEV1",
            notify_team=None,
        )
        restart = RestartServiceArgs(
            service="checkout-api",
            environment="production",
            strategy="immediate",
        )

        assert rollback.target_deployment_id is None
        assert escalation.notify_team is None
        assert restart.strategy == "immediate"


class TestServiceRegistry:
    def test_registers_every_action_kind_with_the_correct_service(self) -> None:
        registry = bootstrap_services()

        assert set(registry) == {case.registry_key for case in SERVICE_CASES}
        for case in SERVICE_CASES:
            proposal = case.proposal_class(
                rationale="The evidence supports this action.",
                args=case.args,
            )

            assert proposal.kind == case.registry_key
            assert isinstance(registry[proposal.kind], case.service_class)

    def test_each_registry_entry_is_an_operational_service(self) -> None:
        registry = bootstrap_services()

        assert all(isinstance(service, Service) for service in registry.values())
        assert len({type(service) for service in registry.values()}) == len(
            SERVICE_CASES
        )

    def test_unknown_action_kind_does_not_resolve(self) -> None:
        registry = bootstrap_services()

        assert registry.get("delete_service") is None  # type: ignore[typeddict-item]


class TestServiceResponseContract:
    def test_success_response_serializes_data_without_an_error(self) -> None:
        response = ServiceSuccessResponse(ok=True, data={"action": "completed"})

        assert response.model_dump(mode="json") == {
            "ok": True,
            "data": {"action": "completed"},
            "error": None,
        }

    @pytest.mark.parametrize(
        "code", ["INVALID_ARGUMENT", "UNKNOWN_TOOL", "EXECUTION_ERROR"]
    )
    def test_error_response_accepts_every_supported_code(self, code: str) -> None:
        response = ServiceErrorResponse(
            ok=False,
            error=ServiceErrorResponseDetail(
                code=code,  # type: ignore[arg-type]
                message="The action could not be executed.",
                input={"service": "checkout-api"},
            ),
        )

        assert response.ok is False
        assert response.data is None
        assert response.error.code == code

    @pytest.mark.parametrize(
        "payload",
        [
            {
                "ok": False,
                "error": {
                    "code": "TIMEOUT",
                    "message": "Unsupported code",
                    "input": {},
                },
            },
            {
                "ok": False,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": "Failure",
                    "input": {},
                    "internal_exception": "secret",
                },
            },
            {
                "ok": True,
                "data": {},
                "error": {"code": "EXECUTION_ERROR", "message": "Failure"},
            },
        ],
    )
    def test_rejects_invalid_response_shapes(self, payload: dict[str, Any]) -> None:
        response_type = (
            ServiceSuccessResponse[Any]
            if payload["ok"] is True
            else ServiceErrorResponse
        )

        with pytest.raises(ValidationError):
            response_type.model_validate(payload)
