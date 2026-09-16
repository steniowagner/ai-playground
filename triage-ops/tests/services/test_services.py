from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError
from triage_ops.services import (
    Service,
    ServiceErrorResponse,
    ServiceErrorResponseDetail,
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
    service_class: type[Service]
    args: BaseModel


SERVICE_CASES = [
    ServiceCase(
        registry_key="rollback_deployment",
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
        service_class=DisableFeatureFlagService,
        args=DisableFeatureFlagServiceArgs(
            service="checkout-api",
            environment="production",
            flag_key="checkout_require_billing_country",
        ),
    ),
    ServiceCase(
        registry_key="restart_service",
        service_class=RestartService,
        args=RestartServiceArgs(
            service="checkout-api",
            environment="production",
            strategy="rolling",
        ),
    ),
    ServiceCase(
        registry_key="escalate_incident",
        service_class=EscalateIncidentService,
        args=EscalateIncidentServiceArgs(
            incident_id="INC-1042",
            to_severity="SEV1",
            notify_team="payments",
        ),
    ),
]


class TestOperationalServices:
    @pytest.mark.parametrize("case", SERVICE_CASES, ids=lambda case: case.registry_key)
    def test_returns_standard_success_with_exact_serialized_arguments(
        self, case: ServiceCase
    ) -> None:
        response = case.service_class().execute(case.args)

        assert isinstance(response, ServiceSuccessResponse)
        assert response.ok is True
        assert response.error is None
        assert response.model_dump(mode="json")["data"] == case.args.model_dump(
            mode="json"
        )

    @pytest.mark.parametrize("case", SERVICE_CASES, ids=lambda case: case.registry_key)
    def test_service_has_a_class_specific_logger(self, case: ServiceCase) -> None:
        service = case.service_class()

        assert service.logger.name == (
            f"{case.service_class.__module__}.{case.service_class.__name__}"
        )


class TestServiceRegistry:
    def test_registers_every_action_kind_with_the_correct_service(self) -> None:
        registry = bootstrap_services()

        assert set(registry) == {case.registry_key for case in SERVICE_CASES}
        for case in SERVICE_CASES:
            assert isinstance(registry[case.registry_key], case.service_class)

    def test_each_registry_entry_is_an_operational_service(self) -> None:
        registry = bootstrap_services()

        assert all(isinstance(service, Service) for service in registry.values())

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
