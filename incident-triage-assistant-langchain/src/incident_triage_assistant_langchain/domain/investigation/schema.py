from typing import Annotated, Literal, TypeAlias

from incident_triage_assistant_langchain.domain.types import IncidentSeverity
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    model_validator,
)

from .proposals import (
    DisableFeatureFlagProposal,
    EscalateIncidentProposal,
    ProposalBase,
    RestartServiceProposal,
    RollbackDeploymentProposal,
)

ConfidenceLevel = Literal["low", "medium", "high"]

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


class AdvisoryAction(ProposalBase):
    """A recommendation with no corresponding tool; displayed, never executed."""

    kind: Literal["advisory"] = Field(
        description=(
            "A recommended next step that none of the other action kinds can "
            "carry out, such as contacting a team, adding monitoring, or opening "
            "a follow-up ticket. Use this rather than forcing a recommendation "
            "into an action kind that does not fit it."
        )
    )

    action: str = Field(
        min_length=1,
        description=(
            "The proposed next step, stated as an instruction to a human "
            "operator. Never describe it as already executed."
        ),
    )


ExecutableProposal: TypeAlias = (
    RollbackDeploymentProposal
    | DisableFeatureFlagProposal
    | RestartServiceProposal
    | EscalateIncidentProposal
)

RecommendedAction: TypeAlias = Annotated[
    ExecutableProposal | AdvisoryAction,
    Field(discriminator="kind"),
]

EXECUTABLE_PROPOSAL_ADAPTER = TypeAdapter(ExecutableProposal)


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
        description=(
            "Evidence-supported proposed actions, or an empty list. Use an "
            "executable action kind only when every one of its arguments was "
            "copied from a successful tool result; otherwise use 'advisory'."
        )
    )

    confidence: ConfidenceLevel = Field(
        description=(
            "Confidence based on the quality, consistency, and completeness of the "
            "available evidence."
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

        for action in self.recommended_actions:
            if (
                isinstance(action, EscalateIncidentProposal)
                and action.args.incident_id != self.incident_id
            ):
                raise ValueError(
                    "An escalation action must target the investigated incident."
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


class InvestigationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: InvestigationOutcome = Field(
        description="A completed investigation when the incident was retrieved, otherwise an investigation failure."
    )
