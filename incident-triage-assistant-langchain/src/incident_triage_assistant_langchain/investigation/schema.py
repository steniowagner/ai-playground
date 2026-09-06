from typing import Literal, TypeAlias

from incident_triage_assistant_langchain.domain.types import IncidentSeverity
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    model_validator,
)

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

    cause: str = Field(
        min_length=1,
        description="A likely explanation inferred from the collected evidence.",
    )
    supporting_evidence: list[str] = Field(
        min_length=1,
        description=(
            "Concise references to observations in the evidence array that support "
            "this cause; do not introduce facts absent from those observations."
        ),
    )


class RecommendedAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    action: str = Field(
        min_length=1,
        description="A proposed next action; never describe it as already executed.",
    )
    rationale: str = Field(
        min_length=1,
        description="Why the collected evidence supports this proposed action.",
    )
    requires_approval: bool = Field(
        description="Whether this action requires human approval before execution."
    )
    approval_action: ApprovalAction | None = Field(
        default=None,
        description=(
            "The controlled action requiring approval, or null when approval is not "
            "required."
        ),
    )

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

    incident_id: str = Field(
        pattern=r"^INC-[0-9]{4}$",
        description="Incident ID copied exactly from the successful get_incident result.",
    )
    summary: str = Field(
        min_length=1,
        description=(
            "Concise completed assessment, including material evidence limitations."
        ),
    )
    severity: IncidentSeverity = Field(
        description=(
            "Authoritative severity copied exactly from the successful get_incident "
            "result; never infer, upgrade, or downgrade it."
        )
    )
    evidence: list[InvestigationEvidence] = Field(
        min_length=1,
        description=(
            "Material observations from successful tool results only; never include "
            "tool errors or unavailable results."
        ),
    )
    likely_causes: list[LikelyCause] = Field(
        description="Evidence-supported likely causes, or an empty list when none are defensible."
    )
    recommended_actions: list[RecommendedAction] = Field(
        description="Evidence-supported proposed actions, or an empty list."
    )
    confidence: ConfidenceLevel = Field(
        description=(
            "Confidence based on the quality, consistency, and completeness of the "
            "available evidence."
        )
    )
    requires_human_approval: bool = Field(
        description=(
            "True exactly when at least one recommended action requires human approval."
        )
    )

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

        approval_required = any(
            action.requires_approval for action in self.recommended_actions
        )
        if self.requires_human_approval != approval_required:
            raise ValueError(
                "'requires_human_approval' must match whether any recommended action "
                "requires approval."
            )

        return self


class InvestigationFailure(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: str = Field(
        pattern=r"^INC-[0-9]{4}$",
        description="The incident ID from the user's investigation request.",
    )
    error_code: Literal["NOT_FOUND", "EXECUTION_ERROR"] = Field(
        description="Why the authoritative incident record could not be retrieved."
    )
    summary: str = Field(
        min_length=1,
        description="A concise safe explanation that the investigation could not proceed.",
    )
    retryable: Literal[False] = Field(
        default=False,
        description="Always false because all permitted incident lookup retries are exhausted.",
    )


InvestigationOutcome: TypeAlias = InvestigationResult | InvestigationFailure

INVESTIGATION_RESPONSE_ADAPTER = TypeAdapter(InvestigationOutcome)


class InvestigationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: InvestigationOutcome = Field(
        description="A completed investigation when the incident was retrieved, otherwise an investigation failure."
    )
