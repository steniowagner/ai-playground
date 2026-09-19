from typing import Any

import pytest
from pydantic import ValidationError
from triage_ops.domain.investigation.proposals import (
    DisableFeatureFlagProposal,
    EscalateIncidentProposal,
    RestartServiceProposal,
    RollbackDeploymentProposal,
)
from triage_ops.domain.investigation.schema import (
    AdvisoryAction,
    InvestigationEvidence,
    InvestigationFailure,
    InvestigationResponse,
    InvestigationResult,
    LikelyCause,
)
from triage_ops.services.disable_feature_flag import DisableFeatureFlagServiceArgs
from triage_ops.services.escalate_incident import EscalateIncidentServiceArgs
from triage_ops.services.restart_service import RestartServiceArgs
from triage_ops.services.rollback_deployment import RollbackDeploymentServiceArgs

from tests.support.factories import make_investigation_result

pytestmark = pytest.mark.unit


def valid_result_data(**overrides: Any) -> dict[str, Any]:
    values = make_investigation_result().model_dump(mode="json")
    values.update(overrides)
    return values


def valid_failure_data(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "incident_id": "INC-1042",
        "error_code": "NOT_FOUND",
        "summary": "The incident record could not be found.",
        "retryable": False,
    }
    values.update(overrides)
    return values


class TestInvestigationResult:
    def test_accepts_complete_result(self) -> None:
        result = InvestigationResult.model_validate(valid_result_data())

        assert result.incident_id == "INC-1042"
        assert result.severity == "SEV2"
        assert result.likely_causes == []
        assert result.recommended_actions == []

    @pytest.mark.parametrize(
        "incident_id",
        ["INC-42", "INC-01042", "inc-1042", "INC_1042", "1042"],
    )
    def test_rejects_malformed_incident_ids(self, incident_id: str) -> None:
        with pytest.raises(ValidationError):
            InvestigationResult.model_validate(
                valid_result_data(incident_id=incident_id)
            )

    def test_rejects_empty_summary(self) -> None:
        with pytest.raises(ValidationError):
            InvestigationResult.model_validate(valid_result_data(summary=""))

    def test_requires_at_least_one_evidence_item(self) -> None:
        with pytest.raises(ValidationError):
            InvestigationResult.model_validate(valid_result_data(evidence=[]))

    @pytest.mark.parametrize(
        "summary",
        [
            "Investigation in progress.",
            "Retrieving the relevant logs.",
            "We will investigate this incident.",
            "Starting the investigation now.",
        ],
    )
    def test_rejects_incomplete_investigation_language(self, summary: str) -> None:
        with pytest.raises(
            ValidationError, match="result describes an incomplete investigation"
        ):
            InvestigationResult.model_validate(valid_result_data(summary=summary))

    @pytest.mark.parametrize("severity", ["SEV1", "SEV2", "SEV3", "SEV4"])
    def test_preserves_supported_severity(self, severity: str) -> None:
        result = InvestigationResult.model_validate(
            valid_result_data(severity=severity)
        )

        assert result.severity == severity

    def test_rejects_unknown_severity(self) -> None:
        with pytest.raises(ValidationError):
            InvestigationResult.model_validate(valid_result_data(severity="SEV5"))

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            InvestigationResult.model_validate(valid_result_data(executed=True))

    def test_is_immutable(self) -> None:
        result = make_investigation_result()

        with pytest.raises(ValidationError, match="Instance is frozen"):
            result.summary = "Changed"  # type: ignore[misc]


class TestInvestigationFailure:
    @pytest.mark.parametrize("error_code", ["NOT_FOUND", "EXECUTION_ERROR"])
    def test_accepts_supported_failure_codes(self, error_code: str) -> None:
        failure = InvestigationFailure.model_validate(
            valid_failure_data(error_code=error_code)
        )

        assert failure.error_code == error_code
        assert failure.retryable is False

    @pytest.mark.parametrize("error_code", ["INVALID_ARGUMENT", "TIMEOUT", ""])
    def test_rejects_unsupported_failure_codes(self, error_code: str) -> None:
        with pytest.raises(ValidationError):
            InvestigationFailure.model_validate(
                valid_failure_data(error_code=error_code)
            )

    def test_retryable_defaults_to_false(self) -> None:
        data = valid_failure_data()
        data.pop("retryable")

        assert InvestigationFailure.model_validate(data).retryable is False

    def test_rejects_retryable_true(self) -> None:
        with pytest.raises(ValidationError):
            InvestigationFailure.model_validate(valid_failure_data(retryable=True))

    @pytest.mark.parametrize("incident_id", ["INC-42", "inc-1042", "1042"])
    def test_rejects_malformed_incident_ids(self, incident_id: str) -> None:
        with pytest.raises(ValidationError):
            InvestigationFailure.model_validate(
                valid_failure_data(incident_id=incident_id)
            )

    def test_rejects_empty_summary_and_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            InvestigationFailure.model_validate(
                valid_failure_data(summary="", internal_error="database unavailable")
            )


class TestEvidenceAndLikelyCauses:
    @pytest.mark.parametrize(
        "source",
        [
            "get_incident",
            "get_service_context",
            "get_recent_deployments",
            "query_metrics",
            "query_logs",
            "get_runbook",
            "get_maintenance_windows",
            "get_feature_flags",
        ],
    )
    def test_accepts_every_supported_evidence_source(self, source: str) -> None:
        evidence = InvestigationEvidence(
            source=source,  # type: ignore[arg-type]
            observation="A material fact returned by the tool.",
        )

        assert evidence.source == source

    def test_rejects_control_flow_tool_as_evidence(self) -> None:
        with pytest.raises(ValidationError):
            InvestigationEvidence(
                source="complete_investigation",  # type: ignore[arg-type]
                observation="Investigation completed.",
            )

    @pytest.mark.parametrize("observation", ["", None])
    def test_rejects_empty_evidence_observations(self, observation: str | None) -> None:
        with pytest.raises(ValidationError):
            InvestigationEvidence(
                source="get_incident",
                observation=observation,  # type: ignore[arg-type]
            )

    def test_accepts_likely_cause_with_supporting_evidence(self) -> None:
        cause = LikelyCause(
            cause="A recent deployment introduced the errors.",
            supporting_evidence=["Error onset followed deployment DEP-104."],
        )

        assert len(cause.supporting_evidence) == 1

    @pytest.mark.parametrize(
        ("cause", "supporting_evidence"),
        [("", ["Observation"]), ("A possible cause", [])],
    )
    def test_rejects_incomplete_likely_causes(
        self, cause: str, supporting_evidence: list[str]
    ) -> None:
        with pytest.raises(ValidationError):
            LikelyCause(cause=cause, supporting_evidence=supporting_evidence)


ACTION_CASES = [
    (
        {
            "kind": "rollback_deployment",
            "rationale": "Errors began after this deployment.",
            "args": {
                "service": "checkout-api",
                "environment": "production",
                "deployment_id": "DEP-104",
                "target_deployment_id": "DEP-103",
            },
        },
        RollbackDeploymentProposal,
        RollbackDeploymentServiceArgs,
    ),
    (
        {
            "kind": "disable_feature_flag",
            "rationale": "The enabled flag correlates with the failures.",
            "args": {
                "service": "checkout-api",
                "environment": "production",
                "flag_key": "new-provider",
            },
        },
        DisableFeatureFlagProposal,
        DisableFeatureFlagServiceArgs,
    ),
    (
        {
            "kind": "restart_service",
            "rationale": "Logs show wedged workers.",
            "args": {
                "service": "checkout-api",
                "environment": "production",
                "strategy": "rolling",
            },
        },
        RestartServiceProposal,
        RestartServiceArgs,
    ),
    (
        {
            "kind": "escalate_incident",
            "rationale": "Observed impact is broader than initially recorded.",
            "args": {
                "incident_id": "INC-1042",
                "to_severity": "SEV1",
                "notify_team": "checkout-oncall",
            },
        },
        EscalateIncidentProposal,
        EscalateIncidentServiceArgs,
    ),
    (
        {
            "kind": "advisory",
            "rationale": "Further validation requires a human operator.",
            "action": "Contact the payment provider.",
        },
        AdvisoryAction,
        None,
    ),
]


class TestRecommendedActions:
    @pytest.mark.parametrize(("payload", "proposal_type", "args_type"), ACTION_CASES)
    def test_discriminates_action_kind_and_validates_arguments(
        self,
        payload: dict[str, Any],
        proposal_type: type,
        args_type: type | None,
    ) -> None:
        result = InvestigationResult.model_validate(
            valid_result_data(recommended_actions=[payload])
        )

        action = result.recommended_actions[0]
        assert isinstance(action, proposal_type)
        if args_type is not None:
            assert isinstance(action.args, args_type)  # type: ignore[union-attr]

    def test_rejects_unknown_action_kind(self) -> None:
        with pytest.raises(ValidationError, match="union_tag_invalid"):
            InvestigationResult.model_validate(
                valid_result_data(
                    recommended_actions=[
                        {
                            "kind": "delete_service",
                            "rationale": "Unsupported action.",
                            "args": {},
                        }
                    ]
                )
            )

    def test_rejects_empty_rationale(self) -> None:
        action = ACTION_CASES[2][0] | {"rationale": ""}

        with pytest.raises(ValidationError):
            InvestigationResult.model_validate(
                valid_result_data(recommended_actions=[action])
            )

    @pytest.mark.parametrize(
        "invalid_args",
        [
            {
                "service": "",
                "environment": "production",
                "strategy": "rolling",
            },
            {
                "service": "checkout-api",
                "environment": "development",
                "strategy": "rolling",
            },
            {
                "service": "checkout-api",
                "environment": "production",
                "strategy": "graceful",
            },
            {
                "service": "checkout-api",
                "environment": "production",
                "strategy": "rolling",
                "force": True,
            },
        ],
    )
    def test_rejects_invalid_executable_action_arguments(
        self, invalid_args: dict[str, Any]
    ) -> None:
        action = ACTION_CASES[2][0] | {"args": invalid_args}

        with pytest.raises(ValidationError):
            InvestigationResult.model_validate(
                valid_result_data(recommended_actions=[action])
            )

    def test_rejects_escalation_for_a_different_incident(self) -> None:
        escalation = ACTION_CASES[3][0] | {
            "args": {
                "incident_id": "INC-9999",
                "to_severity": "SEV1",
                "notify_team": "checkout-oncall",
            }
        }

        with pytest.raises(
            ValidationError, match="must target the investigated incident"
        ):
            InvestigationResult.model_validate(
                valid_result_data(recommended_actions=[escalation])
            )

    def test_proposals_and_arguments_are_immutable(self) -> None:
        proposal = RestartServiceProposal.model_validate(ACTION_CASES[2][0])

        with pytest.raises(ValidationError, match="Instance is frozen"):
            proposal.rationale = "Changed"  # type: ignore[misc]

        with pytest.raises(ValidationError, match="Instance is frozen"):
            proposal.args.strategy = "immediate"  # type: ignore[misc]


class TestInvestigationResponse:
    @pytest.mark.parametrize(
        ("outcome", "outcome_type"),
        [
            (valid_result_data(), InvestigationResult),
            (valid_failure_data(), InvestigationFailure),
        ],
    )
    def test_parses_each_outcome(
        self, outcome: dict[str, Any], outcome_type: type
    ) -> None:
        response = InvestigationResponse.model_validate({"outcome": outcome})

        assert isinstance(response.outcome, outcome_type)

    def test_rejects_unknown_response_fields(self) -> None:
        with pytest.raises(ValidationError):
            InvestigationResponse.model_validate(
                {"outcome": valid_failure_data(), "debug": True}
            )
