from typing import Literal

from pydantic import BaseModel, ConfigDict

from triage_ops.domain import Environment, Service
from triage_ops.tools.get_service_context import (
    ExternalDependecy,
)


class ServicesFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    company: str
    services: list[Service]
    external_dependencies: list[ExternalDependecy]


class FindServiceArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    service: str
    environment: Environment
