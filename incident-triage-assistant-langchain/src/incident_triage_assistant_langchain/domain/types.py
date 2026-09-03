from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Environment = Literal["production", "staging"]

IncidentSeverity = Literal["SEV1", "SEV2", "SEV3", "SEV4"]

ConfidenceLevel = Literal["low", "medium", "high"]

ApprovalAction = Literal[
    "rollback_deployment",
    "disable_feature_flag",
    "restart_service",
    "escalate_incident",
]

EvidenceSource = Literal[
    "get_incident",
    "get_service_context",
    "get_recent_deployments",
    "query_metrics",
    "query_logs",
    "get_runbook",
    "get_maintenance_windows",
    "get_feature_flags",
]


class InvestigationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source: EvidenceSource = Field(description="Tool that produced this evidence.")
    observation: str = Field(
        min_length=1, description="Relevant fact observed in the tool result."
    )


class LikelyCause(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    cause: str = Field(min_length=1)
    supporting_evidence: list[str] = Field(min_length=1)


class RecommendedAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    action: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    requires_approval: bool
    approval_action: ApprovalAction | None = None

    @model_validator(mode="after")
    def validate_approval(self) -> "RecommendedAction":
        if self.requires_approval and self.approval_action is None:
            raise ValueError("'approval_action' is required when approval is required.")

        if not self.requires_approval and self.approval_action is not None:
            raise ValueError(
                "'approval_action' must be omitted when approval is not required."
            )

        return self


class InvestigationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: str = Field(pattern=r"^INC-[0-9]{4}$")
    summary: str = Field(min_length=1)
    severity: IncidentSeverity
    evidence: list[InvestigationEvidence] = Field(min_length=1)
    likely_causes: list[LikelyCause]
    recommended_actions: list[RecommendedAction]
    confidence: ConfidenceLevel
    requires_human_approval: bool

    @model_validator(mode="after")
    def validate_completed_investigation(self) -> "InvestigationResult":
        incomplete_phrases = (
            "in progress",
            "retrieving",
            "will investigate",
            "starting the investigation",
        )

        normalized_summary = self.summary.lower()

        if any(phrase in normalized_summary for phrase in incomplete_phrases):
            raise ValueError("The result describes an incomplete investigation.")

        return self
