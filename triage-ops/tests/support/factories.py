from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from triage_ops.domain.investigation.proposals import RestartServiceProposal
from triage_ops.domain.investigation.schema import (
    InvestigationEvidence,
    InvestigationResult,
)
from triage_ops.services.restart_service import RestartServiceArgs
from triage_ops.tools.get_incident.schema import Incident, IncidentAlert


def make_incident(**overrides: Any) -> Incident:
    values: dict[str, Any] = {
        "incident_id": "INC-1042",
        "title": "Checkout error rate elevated",
        "environment": "production",
        "primary_service": "checkout-api",
        "alert_started_at": datetime(2026, 1, 15, 12, 0, tzinfo=UTC),
        "created_at": datetime(2026, 1, 15, 12, 5, tzinfo=UTC),
        "status": "investigating",
        "severity": "SEV2",
        "reported_symptoms": ["Elevated HTTP 5xx responses"],
        "alert": IncidentAlert(
            metric="http_5xx_rate",
            observed=8.4,
            threshold=2.0,
            unit="percent",
        ),
    }
    values.update(overrides)
    return Incident(**values)


def make_restart_proposal(**overrides: Any) -> RestartServiceProposal:
    values: dict[str, Any] = {
        "rationale": "Workers are wedged according to the retrieved logs.",
        "args": RestartServiceArgs(
            service="checkout-api",
            environment="production",
            strategy="rolling",
        ),
    }
    values.update(overrides)
    return RestartServiceProposal(**values)


def make_investigation_result(**overrides: Any) -> InvestigationResult:
    values: dict[str, Any] = {
        "incident_id": "INC-1042",
        "summary": "Checkout errors correlate with wedged workers.",
        "severity": "SEV2",
        "evidence": [
            InvestigationEvidence(
                source="get_incident",
                observation="The incident reports elevated checkout errors.",
            )
        ],
        "likely_causes": [],
        "recommended_actions": [],
        "confidence": "medium",
    }
    values.update(overrides)
    return InvestigationResult(**values)
