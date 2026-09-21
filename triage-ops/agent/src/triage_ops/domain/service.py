from typing import Any

from pydantic import BaseModel, ConfigDict

from .types import Environment


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
