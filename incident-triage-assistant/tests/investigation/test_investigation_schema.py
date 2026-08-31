import pytest
from incident_triage_assistant.investigation.schema import (
    InvestigationResult,
    RecommendedAction,
)
from pydantic import ValidationError


def valid_result() -> dict[str, object]:
    return {
        "incident_id": "INC-1042",
        "summary": "Checkout errors correlate with a recent production deployment.",
        "severity": "SEV2",
        "evidence": [
            {
                "source": "query_metrics",
                "observation": "Error rate increased after the deployment.",
            }
        ],
        "likely_causes": [
            {
                "cause": "A deployment regression",
                "supporting_evidence": ["Error rate increased after deployment."],
            }
        ],
        "recommended_actions": [],
        "confidence": "high",
        "requires_human_approval": False,
    }


def test_accepts_completed_investigation() -> None:
    result = InvestigationResult.model_validate(valid_result())

    assert result.incident_id == "INC-1042"
    assert result.evidence[0].source == "query_metrics"


def test_rejects_result_without_evidence() -> None:
    raw = valid_result() | {"evidence": []}

    with pytest.raises(ValidationError):
        InvestigationResult.model_validate(raw)


@pytest.mark.parametrize(
    "summary",
    [
        "Investigation is in progress.",
        "Retrieving incident details.",
        "We will investigate the checkout failure.",
        "Starting the investigation now.",
    ],
)
def test_rejects_summary_describing_incomplete_investigation(summary: str) -> None:
    raw = valid_result() | {"summary": summary}

    with pytest.raises(ValidationError):
        InvestigationResult.model_validate(raw)


def test_requires_approval_action_when_action_requires_approval() -> None:
    with pytest.raises(ValidationError):
        RecommendedAction(
            action="Roll back deployment",
            rationale="The deployment correlates with the failure.",
            requires_approval=True,
            approval_action=None,
        )


def test_rejects_approval_action_when_approval_is_not_required() -> None:
    with pytest.raises(ValidationError):
        RecommendedAction(
            action="Continue monitoring",
            rationale="Metrics are recovering.",
            requires_approval=False,
            approval_action="rollback_deployment",
        )
