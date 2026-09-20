from pydantic import BaseModel, ConfigDict

from triage_ops.repositories.incidents import Incident


class GetIncidentsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incidents: list[Incident]


class GetIncidentsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
