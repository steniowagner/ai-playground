from pydantic import BaseModel, ConfigDict, Field

from triage_ops.repositories.incidents import Incident


class GetIncidentArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: str = Field(
        pattern=r"^INC-[0-9]{4}$", description="Incident-id to be used in the search."
    )


class GetIncidentResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incident: Incident
