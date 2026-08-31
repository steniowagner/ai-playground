from typing import Literal

from incident_triage_assistant.tools.get_service_context.schema import (
    ExternalDependecy,
    Service,
)
from pydantic import BaseModel, ConfigDict


class ServicesFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    company: str
    services: list[Service]
    external_dependencies: list[ExternalDependecy]
