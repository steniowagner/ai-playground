from pydantic import BaseModel, ConfigDict, Field

from triage_ops.domain.types import (
    IncidentSeverity,
)


class EscalateIncidentServiceArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: str = Field(
        pattern=r"^INC-[0-9]{4}$",
        description=(
            "Incident to escalate, copied exactly from the successful "
            "get_incident result."
        ),
    )

    to_severity: IncidentSeverity = Field(
        description=(
            "Proposed new severity. SEV1 is the most severe and SEV4 the least, "
            "so this must be more severe than the incident's current severity. "
            "Never propose lowering severity."
        )
    )

    notify_team: str | None = Field(
        default=None,
        description=(
            "Owning team to page, copied exactly from get_service_context "
            "ownership. Null when ownership was not retrieved."
        ),
    )
