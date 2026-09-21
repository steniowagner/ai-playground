from pydantic import BaseModel, ConfigDict

from triage_ops.domain import Environment, Service


class ExternalDependecy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dependency: str
    owner: str
    status_page: str


class GetServiceContextArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment


class GetServiceContextResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: Service
