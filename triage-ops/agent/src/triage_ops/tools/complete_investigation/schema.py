from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CompletionReason = Literal["evidence_sufficient", "incident_lookup_failed"]


class CompleteInvestigationArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: str = Field(
        pattern=r"^INC-[0-9]{4}$",
        description="The incident the investigation was requested for.",
    )
    reason: CompletionReason = Field(
        description=(
            "'evidence_sufficient' when enough evidence was collected to conclude; "
            "'incident_lookup_failed' when get_incident could not be retrieved and "
            "the investigation cannot proceed."
        )
    )


class CompleteInvestigationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    acknowledged: Literal[True] = True
