from typing import Any, Literal

from incident_triage_assistant.domain.types import Environment
from pydantic import BaseModel, ConfigDict


class Service(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    display_name: str
    description: str
    tier: int
    owner_team: str
    on_call: str
    environments: list[Environment]
    dependencies: list[str]
    runbook_ids: list[str]
    slo: dict[str, Any]


class ExternalDependecy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dependency: str
    owner: str
    status_page: str


class ServicesFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    company: str
    services: list[Service]
    external_dependencies: list[ExternalDependecy]


class GetServiceContextArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment


class GetServiceContextResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: Service
