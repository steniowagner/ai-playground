from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from triage_ops.services.disable_feature_flag.schema import (
    DisableFeatureFlagServiceArgs,
)
from triage_ops.services.escalate_incident.schema import (
    EscalateIncidentServiceArgs,
)
from triage_ops.services.restart_service.schema import (
    RestartServiceArgs,
)
from triage_ops.services.rollback_deployment.schema import (
    RollbackDeploymentServiceArgs,
)


class ProposalBase(BaseModel):
    """
    Shared contract for every recommended action.

    Deliberately absent: any field describing whether approval is required, how
    reversible the action is, or how wide its blast radius is. Those are static
    properties of the tool that would execute the action, resolved by the
    execution graph. A model-supplied value could be wrong or adversarially
    influenced by tool output, and must never gate a mutation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    rationale: str = Field(
        min_length=1,
        description=(
            "Why the collected evidence supports proposing this action. Reference "
            "only observations already present in the evidence array. Never state "
            "or imply that the action has been executed."
        ),
    )


class DisableFeatureFlagProposal(ProposalBase):
    """Proposes turning off a feature flag for a service and environment."""

    kind: Literal["disable_feature_flag"] = Field(
        description=(
            "Propose disabling a feature flag. Use only when a specific flag was "
            "retrieved from get_feature_flags and its state or recent change is "
            "associated with the incident by evidence."
        ),
        default="disable_feature_flag",
    )

    args: DisableFeatureFlagServiceArgs


class EscalateIncidentProposal(ProposalBase):
    """Proposes raising incident severity and notifying an owning team."""

    kind: Literal["escalate_incident"] = Field(
        description=(
            "Propose raising the incident's severity. Use only when evidence "
            "shows impact materially broader than the recorded severity "
            "reflects. This changes incident records and paging, not the "
            "behaviour of any service."
        ),
        default="escalate_incident",
    )

    args: EscalateIncidentServiceArgs


class RestartServiceProposal(ProposalBase):
    """Proposes restarting instances of a service."""

    kind: Literal["restart_service"] = Field(
        description=(
            "Propose restarting a service. Use only when evidence indicates a "
            "recoverable process-level condition such as exhausted connections, "
            "leaked memory, or wedged workers. Never propose a restart merely "
            "because the cause is unclear."
        ),
        default="restart_service",
    )

    args: RestartServiceArgs


class RollbackDeploymentProposal(ProposalBase):
    """Proposes reverting a service to a previously deployed revision."""

    kind: Literal["rollback_deployment"] = Field(
        description=(
            "Propose reverting a deployment. Use only when a specific deployment "
            "was retrieved from get_recent_deployments and the evidence associates "
            "it with the incident onset."
        ),
        default="rollback_deployment",
    )

    args: RollbackDeploymentServiceArgs
