from pydantic import BaseModel, ConfigDict

from ..get_incident import Incident


class GetIncidentsResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    incidents: list[Incident]


class GetIncidentsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
